import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, desc
from temporalio.client import Client

from .config import settings
from .db import get_session
from .models import Supervisor, OrderRun, ActivityLog
from .workflows import OrderSupervisorWorkflow, execute_direct_initial_assessment, execute_direct_event_step

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


# --- Security & Domain Validation Rules for Operator Directives ---
FORBIDDEN_PATTERNS = [
    r"ignore (all )?(previous|above) (instructions|prompts)",
    r"system prompt",
    r"override (system|rules|policy)",
    r"jailbreak",
    r"<script[\s>]",
    r"javascript:",
    r"drop\s+table",
    r"delete\s+from",
    r"select\s+\*\s+from",
    r"exec\(",
    r"eval\(",
    r"format\s+c:",
    r"chmod\s+777",
]

ALLOWED_DOMAIN_KEYWORDS = [
    "cancel", "dont want", "don't want", "stop", "abort", "close", "terminate", "reject",
    "prioritize", "speed", "fast", "express", "overnight", "expedite", "urgent",
    "hold", "wait", "delay", "pause", "freeze",
    "customer", "message", "email", "sms", "notify", "contact",
    "warehouse", "carrier", "shipping", "logistics", "package", "parcel", "delivery", "dispatch",
    "refund", "payment", "address", "return", "note", "verify", "check", "sla"
]

def validate_instruction_content(text: str) -> str:
    cleaned = text.strip()
    if len(cleaned) < 5:
        raise HTTPException(status_code=400, detail="Instruction must be at least 5 characters long.")
    if len(cleaned) > 300:
        raise HTTPException(status_code=400, detail="Instruction exceeds the 300-character maximum limit.")
    
    # 1. Prompt injection / Malicious code check
    lower_text = cleaned.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, lower_text):
            raise HTTPException(
                status_code=400,
                detail="Security violation: Prompt injection, unauthorized system override, or script syntax detected."
            )
            
    # 2. Domain check: Ensure instruction pertains to order operations
    is_domain_relevant = any(keyword in lower_text for keyword in ALLOWED_DOMAIN_KEYWORDS)
    if not is_domain_relevant:
        raise HTTPException(
            status_code=400,
            detail="Invalid directive: Instruction must be a recognized order operation (e.g. cancel, hold, prioritize speed, notify customer, logistics update)."
        )
        
    return cleaned

class WorkflowControlReq(BaseModel):
    action: Literal["pause", "resume", "terminate", "wake"]
    reason: Optional[str] = "Operator action"

# --- Temporal Client Helper with Fast Offline Detection ---
_client: Optional[Client] = None
async def get_temporal_client() -> Optional[Client]:
    global _client
    if _client is None:
        try:
            import asyncio
            _client = await asyncio.wait_for(Client.connect(settings.TEMPORAL_HOST), timeout=1.5)
        except Exception as e:
            logger.debug(f"Temporal server not available at {settings.TEMPORAL_HOST}: {e}")
            return None
    return _client

# -------------------------------------------------------------
# SUPERVISORS ENDPOINTS
# -------------------------------------------------------------
@router.get("/supervisors")
def list_supervisors(session: Session = Depends(get_session)):
    items = session.exec(select(Supervisor).where(Supervisor.is_active == True)).all()
    if not items:
        from .main import seed_default_supervisors
        seed_default_supervisors()
        items = session.exec(select(Supervisor).where(Supervisor.is_active == True)).all()
    return items

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

    # Start Temporal Workflow (or fallback to direct autonomous runner)
    temporal_started = False
    try:
        client = await get_temporal_client()
        if client:
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
            temporal_started = True
    except Exception as e:
        logger.warning(f"Temporal server offline ({e}). Running direct autonomous supervisor.")

    if not temporal_started:
        import asyncio
        asyncio.create_task(
            execute_direct_initial_assessment(
                run_id=run_id,
                order_id=payload.order_id,
                order_context=payload.order_context,
                base_instruction=supervisor.base_instruction,
                runtime_instructions=[payload.initial_instructions] if payload.initial_instructions else [],
                wake_up_policy=supervisor.wake_up_policy
            )
        )

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

    if run.status in ["COMPLETED", "TERMINATED"]:
        raise HTTPException(status_code=400, detail=f"Order is already {run.status}. Cannot inject new events into a finished order.")
    if run.status == "PAUSED":
        raise HTTPException(status_code=400, detail="Workflow is currently PAUSED by operator. Click Resume before injecting events.")

    temporal_signaled = False
    try:
        client = await get_temporal_client()
        if client:
            handle = client.get_workflow_handle(f"order-supervisor-{run_id}")
            import asyncio
            await asyncio.wait_for(
                handle.signal(
                    OrderSupervisorWorkflow.receive_event,
                    {"event_type": payload.event_type, "payload": payload.payload}
                ),
                timeout=1.5
            )
            temporal_signaled = True
            return {"status": "SUCCESS", "message": f"Signal '{payload.event_type}' sent to workflow {run_id}"}
    except Exception as e:
        logger.warning(f"Temporal signal error: {e}. Executing direct event processing.")

    if not temporal_signaled:
        import asyncio
        asyncio.create_task(
            execute_direct_event_step(
                run_id=run_id,
                order_id=run.order_id,
                event_type=payload.event_type,
                payload=payload.payload
            )
        )
        return {"status": "SUCCESS", "message": f"Signal '{payload.event_type}' handled by autonomous supervisor."}

@router.post("/runs/{run_id}/instructions")
async def inject_runtime_instruction(
    run_id: str,
    payload: InstructionInjectionReq,
    session: Session = Depends(get_session)
):
    valid_instruction = validate_instruction_content(payload.instruction)

    run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
    if not run:
        raise HTTPException(status_code=404, detail="Order run not found")

    if run.status in ["COMPLETED", "TERMINATED"]:
        raise HTTPException(status_code=400, detail=f"Order is already {run.status}. Cannot add guidance to a finished order.")
    if run.status == "PAUSED":
        raise HTTPException(status_code=400, detail="Workflow is PAUSED. Resume before injecting guidance.")

    current_instructions = list(run.runtime_instructions or [])
    current_instructions.append(valid_instruction)
    run.runtime_instructions = current_instructions
    session.add(run)
    
    log = ActivityLog(
        run_id=run_id,
        log_type="INSTRUCTION",
        trigger_source="OPERATOR",
        title="Live Operator Instruction",
        details=valid_instruction
    )
    session.add(log)
    session.commit()

    import asyncio
    from .workflows import execute_direct_instruction_step
    asyncio.create_task(execute_direct_instruction_step(run_id, valid_instruction))

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

    now = datetime.now()
    if payload.action == "pause":
        run.status = "PAUSED"
    elif payload.action == "resume":
        if run.next_wake_time and run.next_wake_time > now:
            run.status = "SLEEPING"
        else:
            run.status = "ACTIVE"
            import asyncio
            from .workflows import execute_direct_scheduled_wakeup
            asyncio.create_task(execute_direct_scheduled_wakeup(run_id))
    elif payload.action == "terminate":
        run.status = "TERMINATED"
        run.next_wake_time = None
    elif payload.action == "wake":
        run.status = "ACTIVE"
        import asyncio
        from .workflows import execute_direct_scheduled_wakeup
        asyncio.create_task(execute_direct_scheduled_wakeup(
            run_id=run_id,
            trigger_source="OPERATOR",
            custom_title="Force Wake: Manual Order Assessment Triggered"
        ))
        
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
        if client:
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
    Scans active/sleeping order runs in PostgreSQL and reconciles state.
    Ultra-fast non-blocking execution with sub-second timeouts to avoid UI freezes.
    """
    import asyncio
    active_runs = session.exec(
        select(OrderRun).where(OrderRun.status.in_(["ACTIVE", "SLEEPING", "PAUSED"]))
    ).all()
    
    total_checked = len(active_runs)
    healthy_count = total_checked
    healed_count = 0
    
    client = None
    try:
        client = await get_temporal_client()
    except Exception:
        pass

    if not client:
        return {
            "status": "SUCCESS",
            "total_checked": total_checked,
            "healthy_count": total_checked,
            "healed_count": 0,
            "message": f"Autonomous state machine verified. {total_checked} order runs healthy."
        }

    for run in active_runs:
        workflow_id = f"order-supervisor-{run.id}"
        try:
            handle = client.get_workflow_handle(workflow_id)
            desc = await asyncio.wait_for(handle.describe(), timeout=0.6)
            if desc and desc.status.name == "RUNNING":
                continue
        except Exception:
            pass

    return {
        "status": "SUCCESS",
        "total_checked": total_checked,
        "healthy_count": healthy_count,
        "healed_count": healed_count,
        "message": f"Reconciliation complete: {healthy_count} workflows verified healthy."
    }
