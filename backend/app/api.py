import uuid
import logging
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, desc
from temporalio.client import Client

from .config import settings
from .db import get_session
from .models import Supervisor, OrderRun, ActivityLog
from .workflows import OrderSupervisorWorkflow

router = APIRouter(prefix="/v1")
logger = logging.getLogger(__name__)

# --- In-File Request Payloads (No Schemas folder required) ---
class OrderRunCreateReq(BaseModel):
    order_id: str
    supervisor_id: Optional[str] = None
    order_context: Dict[str, Any] = Field(default_factory=dict)
    initial_instructions: Optional[str] = None

class EventInjectionReq(BaseModel):
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class InstructionInjectionReq(BaseModel):
    instruction: str

class WorkflowControlReq(BaseModel):
    action: Literal["pause", "resume", "terminate", "wake"]
    reason: Optional[str] = "Operator action"

# --- Temporal Client Helper ---
_client: Optional[Client] = None
async def get_temporal_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect(settings.TEMPORAL_HOST)
    return _client

# -------------------------------------------------------------
# SUPERVISORS ENDPOINTS
# -------------------------------------------------------------
@router.get("/supervisors")
def list_supervisors(session: Session = Depends(get_session)):
    return session.exec(select(Supervisor).where(Supervisor.is_active == True)).all()

@router.post("/supervisors")
def create_supervisor(payload: Dict[str, Any], session: Session = Depends(get_session)):
    sup = Supervisor(**payload)
    session.add(sup)
    session.commit()
    session.refresh(sup)
    return sup

@router.get("/supervisors/{supervisor_id}")
def get_supervisor(supervisor_id: str, session: Session = Depends(get_session)):
    sup = session.exec(select(Supervisor).where(Supervisor.id == supervisor_id)).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    return sup

@router.put("/supervisors/{supervisor_id}")
def update_supervisor(supervisor_id: str, payload: Dict[str, Any], session: Session = Depends(get_session)):
    sup = session.exec(select(Supervisor).where(Supervisor.id == supervisor_id)).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    for k, v in payload.items():
        if hasattr(sup, k):
            setattr(sup, k, v)
    session.add(sup)
    session.commit()
    session.refresh(sup)
    return sup

# -------------------------------------------------------------
# ORDER RUNS & SIMULATOR ENDPOINTS
# -------------------------------------------------------------
@router.post("/runs")
async def create_order_run(payload: OrderRunCreateReq, session: Session = Depends(get_session)):
    supervisor = None
    if payload.supervisor_id:
        supervisor = session.exec(select(Supervisor).where(Supervisor.id == payload.supervisor_id)).first()
    if not supervisor:
        supervisor = session.exec(select(Supervisor)).first()
    if not supervisor:
        supervisor = Supervisor(
            name="Default E-commerce Supervisor",
            description="Standard supervisor for retail and e-commerce orders."
        )
        session.add(supervisor)
        session.commit()
        session.refresh(supervisor)

    run_id = f"run_{uuid.uuid4().hex[:10]}"
    
    order_run = OrderRun(
        id=run_id,
        order_id=payload.order_id,
        supervisor_id=supervisor.id,
        status="ACTIVE",
        order_context=payload.order_context,
        compact_memory=f"Order #{payload.order_id} placed. Supervisor {supervisor.name} attached.",
        runtime_instructions=[payload.initial_instructions] if payload.initial_instructions else []
    )
    session.add(order_run)
    session.commit()
    session.refresh(order_run)

    # Start Temporal Workflow
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            OrderSupervisorWorkflow.run,
            {
                "run_id": run_id,
                "order_id": payload.order_id,
                "supervisor_id": supervisor.id,
                "order_context": payload.order_context,
                "base_instruction": supervisor.base_instruction,
                "wake_up_policy": supervisor.wake_up_policy,
                "initial_instructions": payload.initial_instructions
            },
            id=f"order-supervisor-{run_id}",
            task_queue=settings.TEMPORAL_TASK_QUEUE
        )
    except Exception as e:
        logger.warning(f"Temporal server trigger: {e}")

    return order_run

@router.get("/runs")
def list_order_runs(
    status: Optional[str] = None,
    order_id: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    session: Session = Depends(get_session)
):
    query = select(OrderRun).order_by(desc(OrderRun.created_at))
    if status and status.upper() != "ALL":
        query = query.where(OrderRun.status == status.upper())
    if order_id:
        query = query.where(OrderRun.order_id.contains(order_id))
        
    items = session.exec(query.offset(offset).limit(limit)).all()
    total = len(session.exec(select(OrderRun)).all())
    return {"items": items, "total": total}

@router.get("/runs/{run_id}")
def get_order_run(run_id: str, session: Session = Depends(get_session)):
    run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Order run not found")
    return run

@router.get("/runs/{run_id}/timeline")
def get_order_timeline(run_id: str, session: Session = Depends(get_session)):
    logs = session.exec(
        select(ActivityLog)
        .where(ActivityLog.run_id == run_id)
        .order_by(desc(ActivityLog.timestamp))
    ).all()
    return logs

@router.post("/runs/{run_id}/events")
async def inject_order_event(
    run_id: str,
    payload: EventInjectionReq,
    session: Session = Depends(get_session)
):
    run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Order run not found")

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(f"order-supervisor-{run_id}")
        await handle.signal(
            OrderSupervisorWorkflow.receive_event,
            {"event_type": payload.event_type, "payload": payload.payload}
        )
        return {"status": "SUCCESS", "message": f"Signal '{payload.event_type}' sent to workflow {run_id}"}
    except Exception as e:
        logger.error(f"Temporal signal error: {e}")
        log = ActivityLog(
            run_id=run_id,
            log_type="EVENT",
            trigger_source="SIMULATOR",
            title=f"Injected Event: {payload.event_type}",
            details=str(payload.payload),
            metadata_payload={"event_type": payload.event_type, "payload": payload.payload}
        )
        session.add(log)
        session.commit()
        return {"status": "RECORDED_DB_ONLY", "message": f"Recorded to DB (Temporal offline: {str(e)})"}

@router.post("/runs/{run_id}/instructions")
async def inject_runtime_instruction(
    run_id: str,
    payload: InstructionInjectionReq,
    session: Session = Depends(get_session)
):
    run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Order run not found")

    current_instructions = list(run.runtime_instructions or [])
    current_instructions.append(payload.instruction)
    run.runtime_instructions = current_instructions
    session.add(run)
    
    log = ActivityLog(
        run_id=run_id,
        log_type="INSTRUCTION",
        trigger_source="OPERATOR",
        title="Live Operator Instruction",
        details=payload.instruction
    )
    session.add(log)
    session.commit()

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(f"order-supervisor-{run_id}")
        await handle.signal(
            OrderSupervisorWorkflow.receive_instruction,
            {"instruction": payload.instruction}
        )
    except Exception as e:
        logger.warning(f"Temporal instruction signal error: {e}")

    return {"status": "SUCCESS", "message": "Instruction added to run context"}

@router.post("/runs/{run_id}/controls")
async def control_workflow(
    run_id: str,
    payload: WorkflowControlReq,
    session: Session = Depends(get_session)
):
    run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Order run not found")

    if payload.action == "pause":
        run.status = "PAUSED"
    elif payload.action == "resume":
        run.status = "ACTIVE"
    elif payload.action == "terminate":
        run.status = "TERMINATED"
        
    session.add(run)
    
    log = ActivityLog(
        run_id=run_id,
        log_type="CONTROL",
        trigger_source="OPERATOR",
        title=f"Workflow Control: {payload.action.upper()}",
        details=payload.reason
    )
    session.add(log)
    session.commit()

    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(f"order-supervisor-{run_id}")
        await handle.signal(
            OrderSupervisorWorkflow.receive_control,
            {"action": payload.action, "reason": payload.reason}
        )
    except Exception as e:
        logger.warning(f"Temporal control signal error: {e}")

    return {"status": "SUCCESS", "message": f"Workflow {payload.action} action executed"}

# -------------------------------------------------------------
# WORKFLOW HEALTH & RECONCILIATION / SELF-HEALING ENGINE
# -------------------------------------------------------------
@router.post("/reconcile")
async def reconcile_workflows(session: Session = Depends(get_session)):
    """
    Scans all active/sleeping order runs in PostgreSQL and reconciles their state
    with Temporal, self-healing any desynced or missing workflows.
    """
    active_runs = session.exec(
        select(OrderRun).where(OrderRun.status.in_(["ACTIVE", "SLEEPING", "PAUSED"]))
    ).all()
    
    total_checked = len(active_runs)
    healthy_count = 0
    healed_count = 0
    
    try:
        client = await get_temporal_client()
    except Exception as e:
        logger.warning(f"Temporal connection during reconciliation: {e}")
        return {
            "status": "TEMPORAL_OFFLINE",
            "total_checked": total_checked,
            "healthy_count": 0,
            "healed_count": 0,
            "message": f"Temporal server unreachable ({e}). Database state intact."
        }

    for run in active_runs:
        workflow_id = f"order-supervisor-{run.id}"
        is_running_in_temporal = False
        
        try:
            handle = client.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            if desc.status.name == "RUNNING":
                is_running_in_temporal = True
                healthy_count += 1
        except Exception:
            is_running_in_temporal = False

        if not is_running_in_temporal:
            try:
                supervisor = session.exec(select(Supervisor).where(Supervisor.id == run.supervisor_id)).first()
                base_instr = supervisor.base_instruction if supervisor else "You are an autonomous Order Supervisor."
                wake_policy = supervisor.wake_up_policy if supervisor else "balanced"
                
                await client.start_workflow(
                    OrderSupervisorWorkflow.run,
                    {
                        "run_id": run.id,
                        "order_id": run.order_id,
                        "supervisor_id": run.supervisor_id,
                        "order_context": run.order_context,
                        "base_instruction": base_instr,
                        "wake_up_policy": wake_policy,
                        "initial_instructions": run.runtime_instructions[-1] if run.runtime_instructions else None
                    },
                    id=workflow_id,
                    task_queue=settings.TEMPORAL_TASK_QUEUE
                )
                
                healed_log = ActivityLog(
                    run_id=run.id,
                    log_type="CONTROL",
                    trigger_source="OPERATOR",
                    title="Self-Healing: Workflow Reconnected",
                    details="Temporal workflow was disconnected and has been automatically re-instantiated and synchronized with PostgreSQL state.",
                    metadata_payload={"workflow_id": workflow_id, "action": "SELF_HEAL"}
                )
                session.add(healed_log)
                healed_count += 1
            except Exception as e:
                logger.error(f"Failed to self-heal workflow {run.id}: {e}")

    session.commit()
    return {
        "status": "SUCCESS",
        "total_checked": total_checked,
        "healthy_count": healthy_count,
        "healed_count": healed_count,
        "message": f"Reconciliation complete: {healthy_count} healthy, {healed_count} self-healed."
    }
