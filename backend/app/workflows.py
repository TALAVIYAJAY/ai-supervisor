import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from temporalio import workflow, activity
from sqlmodel import Session, select

with workflow.unsafe.imports_passed_through():
    from .db import engine
    from .models import OrderRun, ActivityLog
    from .services import classify_event, run_agent_reasoning_step, generate_final_learnings

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# TEMPORAL ACTIVITIES
# -------------------------------------------------------------
@activity.defn
async def classify_event_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    return classify_event(
        event_type=params.get("event_type", "unknown"),
        payload=params.get("payload", {}),
        compact_memory=params.get("compact_memory", ""),
        wake_up_policy=params.get("wake_up_policy", "balanced")
    )

@activity.defn
async def run_agent_step_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    return run_agent_reasoning_step(
        order_id=params.get("order_id"),
        order_context=params.get("order_context", {}),
        base_instruction=params.get("base_instruction", ""),
        runtime_instructions=params.get("runtime_instructions", []),
        compact_memory=params.get("compact_memory", ""),
        trigger_event=params.get("trigger_event", {}),
        trigger_source=params.get("trigger_source", "SIGNAL")
    )

@activity.defn
async def record_activity_log_activity(params: Dict[str, Any]) -> None:
    with Session(engine) as session:
        log_entry = ActivityLog(
            run_id=params["run_id"],
            log_type=params["log_type"],
            trigger_source=params.get("trigger_source", "SIGNAL"),
            title=params["title"],
            details=params.get("details"),
            metadata_payload=params.get("metadata_payload", {}),
            timestamp=datetime.now()
        )
        session.add(log_entry)
        session.commit()

@activity.defn
async def update_order_run_state_activity(params: Dict[str, Any]) -> None:
    run_id = params["run_id"]
    with Session(engine) as session:
        run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
        if run:
            if "status" in params:
                run.status = params["status"]
            if "compact_memory" in params:
                run.compact_memory = params["compact_memory"]
            if "runtime_instructions" in params:
                run.runtime_instructions = params["runtime_instructions"]
            if "next_wake_time" in params:
                run.next_wake_time = datetime.fromisoformat(params["next_wake_time"]) if params["next_wake_time"] else None
            if "last_wake_time" in params:
                run.last_wake_time = datetime.fromisoformat(params["last_wake_time"]) if params["last_wake_time"] else None
            if "final_summary" in params:
                run.final_summary = params["final_summary"]
            run.updated_at = datetime.now()
            session.add(run)
            session.commit()

@activity.defn
async def finalize_run_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    order_id = params.get("order_id")
    order_context = params.get("order_context", {})
    compact_memory = params.get("compact_memory", "")
    runtime_instructions = params.get("runtime_instructions", [])
    run_id = params.get("run_id")
    
    with Session(engine) as session:
        logs = session.exec(select(ActivityLog).where(ActivityLog.run_id == run_id)).all()
        activity_history = [{"title": l.title, "type": l.log_type, "details": l.details} for l in logs]
        
    final_report = generate_final_learnings(
        order_id=order_id,
        order_context=order_context,
        compact_memory=compact_memory,
        activity_history=activity_history,
        runtime_instructions=runtime_instructions
    )
    
    with Session(engine) as session:
        summary_log = ActivityLog(
            run_id=run_id,
            log_type="FINAL_SUMMARY",
            trigger_source="TERMINAL",
            title="Order Lifecycle Concluded - Post-Mortem Generated",
            details=final_report.get("final_summary", "Run completed."),
            metadata_payload=final_report,
            timestamp=datetime.now()
        )
        session.add(summary_log)
        
        run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
        if run:
            run.status = "COMPLETED"
            run.final_summary = final_report
            run.updated_at = datetime.now()
            session.add(run)
            
        session.commit()
        
    return final_report

# -------------------------------------------------------------
# TEMPORAL WORKFLOW DEFINITION
# -------------------------------------------------------------
@workflow.defn
class OrderSupervisorWorkflow:
    def __init__(self):
        self.run_id: str = ""
        self.order_id: str = ""
        self.supervisor_id: str = ""
        self.order_context: Dict[str, Any] = {}
        self.base_instruction: str = ""
        self.wake_up_policy: str = "balanced"
        self.runtime_instructions: List[str] = []
        
        self.status: str = "ACTIVE"
        self.compact_memory: str = "Order workflow started."
        self.pending_events: List[Dict[str, Any]] = []
        self.pending_instructions: List[str] = []
        
        self.is_running: bool = True
        self.is_paused: bool = False
        self.is_terminated: bool = False
        
        self.sleep_duration_seconds: int = 1800
        self.next_wake_time: Optional[datetime] = None

    @workflow.signal(name="event_signal")
    async def receive_event(self, event_data: Dict[str, Any]):
        self.pending_events.append(event_data)

    @workflow.signal(name="instruction_signal")
    async def receive_instruction(self, instruction_data: Dict[str, Any]):
        text = instruction_data.get("instruction", "")
        if text:
            self.runtime_instructions.append(text)
            self.pending_instructions.append(text)

    @workflow.signal(name="control_signal")
    async def receive_control(self, control_data: Dict[str, Any]):
        action = control_data.get("action")
        now = datetime.now()
        if action == "pause":
            self.is_paused = True
            self.status = "PAUSED"
        elif action == "resume":
            self.is_paused = False
            if self.next_wake_time and self.next_wake_time > now:
                self.status = "SLEEPING"
            else:
                self.status = "ACTIVE"
        elif action == "terminate":
            self.is_terminated = True
            self.is_running = False
            self.status = "TERMINATED"
            self.next_wake_time = None
        elif action == "wake":
            self.sleep_duration_seconds = 0

    @workflow.query(name="get_state")
    def get_state(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "order_id": self.order_id,
            "status": self.status,
            "compact_memory": self.compact_memory,
            "runtime_instructions": self.runtime_instructions,
            "next_wake_time": self.next_wake_time.isoformat() if self.next_wake_time else None,
            "is_paused": self.is_paused,
            "is_running": self.is_running
        }

    @workflow.run
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.run_id = input_data["run_id"]
        self.order_id = input_data["order_id"]
        self.supervisor_id = input_data.get("supervisor_id", "")
        self.order_context = input_data.get("order_context", {})
        self.base_instruction = input_data.get("base_instruction", "")
        self.wake_up_policy = input_data.get("wake_up_policy", "balanced")
        
        if input_data.get("initial_instructions"):
            self.runtime_instructions.append(input_data["initial_instructions"])

        # 1. Log Workflow Start
        await workflow.execute_activity(
            record_activity_log_activity,
            {
                "run_id": self.run_id,
                "log_type": "EVENT",
                "trigger_source": "START",
                "title": f"Order #{self.order_id} Workflow Started",
                "details": f"Initialized with supervisor policy '{self.wake_up_policy}'.",
                "metadata_payload": self.order_context
            },
            start_to_close_timeout=timedelta(seconds=15)
        )

        # 2. Initial Assessment
        initial_agent_result = await workflow.execute_activity(
            run_agent_step_activity,
            {
                "order_id": self.order_id,
                "order_context": self.order_context,
                "base_instruction": self.base_instruction,
                "runtime_instructions": self.runtime_instructions,
                "compact_memory": self.compact_memory,
                "trigger_event": {"event_type": "order_created", "payload": self.order_context},
                "trigger_source": "START"
            },
            start_to_close_timeout=timedelta(seconds=45)
        )

        self.compact_memory = initial_agent_result.get("compact_memory", self.compact_memory)
        self.sleep_duration_seconds = initial_agent_result.get("sleep_minutes", 30) * 60
        self.next_wake_time = datetime.now() + timedelta(seconds=self.sleep_duration_seconds)
        self.status = "SLEEPING"

        await workflow.execute_activity(
            record_activity_log_activity,
            {
                "run_id": self.run_id,
                "log_type": "REASONING",
                "trigger_source": "START",
                "title": "Initial Order Assessment",
                "details": initial_agent_result.get("thoughts", "Initial review complete."),
                "metadata_payload": {
                    "tool_actions": initial_agent_result.get("tool_actions", []),
                    "compact_memory": self.compact_memory,
                    "next_wake_minutes": initial_agent_result.get("sleep_minutes", 30)
                }
            },
            start_to_close_timeout=timedelta(seconds=15)
        )

        await workflow.execute_activity(
            update_order_run_state_activity,
            {
                "run_id": self.run_id,
                "status": self.status,
                "compact_memory": self.compact_memory,
                "next_wake_time": self.next_wake_time.isoformat()
            },
            start_to_close_timeout=timedelta(seconds=15)
        )

        # 3. Main Workflow Event-Driven & Timer Loop
        while self.is_running and not self.is_terminated:
            if self.is_paused:
                await workflow.wait_condition(lambda: not self.is_paused or self.is_terminated)
                if self.is_terminated:
                    break

            now = datetime.now()
            remaining_seconds = max(1, int((self.next_wake_time - now).total_seconds())) if self.next_wake_time else 1800

            signal_received = False
            try:
                await workflow.wait_condition(
                    lambda: len(self.pending_events) > 0 or len(self.pending_instructions) > 0 or self.is_terminated,
                    timeout=timedelta(seconds=remaining_seconds)
                )
                signal_received = True
            except asyncio.TimeoutError:
                signal_received = False

            if self.is_terminated:
                break

            if self.pending_instructions:
                instr = self.pending_instructions.pop(0)
                await workflow.execute_activity(
                    record_activity_log_activity,
                    {
                        "run_id": self.run_id,
                        "log_type": "INSTRUCTION",
                        "trigger_source": "OPERATOR",
                        "title": "Live Operator Instruction Received",
                        "details": instr
                    },
                    start_to_close_timeout=timedelta(seconds=15)
                )

            # Event Signal Received -> Tier-1 Classifier
            if signal_received and self.pending_events:
                event_data = self.pending_events.pop(0)
                event_type = event_data.get("event_type", "unknown")
                payload = event_data.get("payload", {})

                await workflow.execute_activity(
                    record_activity_log_activity,
                    {
                        "run_id": self.run_id,
                        "log_type": "EVENT",
                        "trigger_source": "SIGNAL",
                        "title": f"Incoming Signal: {event_type}",
                        "details": f"Payload: {payload}",
                        "metadata_payload": event_data
                    },
                    start_to_close_timeout=timedelta(seconds=15)
                )

                classify_result = await workflow.execute_activity(
                    classify_event_activity,
                    {
                        "event_type": event_type,
                        "payload": payload,
                        "compact_memory": self.compact_memory,
                        "wake_up_policy": self.wake_up_policy
                    },
                    start_to_close_timeout=timedelta(seconds=20)
                )

                decision = classify_result.get("decision", "WAKE_NOW")
                urgency = classify_result.get("urgency", "MEDIUM")
                reasoning = classify_result.get("reasoning", "")

                await workflow.execute_activity(
                    record_activity_log_activity,
                    {
                        "run_id": self.run_id,
                        "log_type": "CLASSIFICATION",
                        "trigger_source": "SIGNAL",
                        "title": f"Classifier Decision: {decision} ({urgency})",
                        "details": reasoning,
                        "metadata_payload": classify_result
                    },
                    start_to_close_timeout=timedelta(seconds=15)
                )

                if decision == "WAKE_NOW":
                    self.status = "ACTIVE"
                    agent_result = await workflow.execute_activity(
                        run_agent_step_activity,
                        {
                            "order_id": self.order_id,
                            "order_context": self.order_context,
                            "base_instruction": self.base_instruction,
                            "runtime_instructions": self.runtime_instructions,
                            "compact_memory": self.compact_memory,
                            "trigger_event": event_data,
                            "trigger_source": "SIGNAL"
                        },
                        start_to_close_timeout=timedelta(seconds=45)
                    )
                    
                    self.compact_memory = agent_result.get("compact_memory", self.compact_memory)
                    self.sleep_duration_seconds = agent_result.get("sleep_minutes", 30) * 60
                    self.next_wake_time = datetime.now() + timedelta(seconds=self.sleep_duration_seconds)
                    
                    if agent_result.get("is_escalated"):
                        self.status = "ESCALATED"
                    elif agent_result.get("is_terminal") or event_type in ["delivered", "order_delivered", "refund_completed"]:
                        self.is_running = False
                        self.status = "COMPLETED"
                    else:
                        self.status = "SLEEPING"

                    await workflow.execute_activity(
                        record_activity_log_activity,
                        {
                            "run_id": self.run_id,
                            "log_type": "REASONING",
                            "trigger_source": "SIGNAL",
                            "title": f"Agent Action on '{event_type}'",
                            "details": agent_result.get("thoughts", "Action executed."),
                            "metadata_payload": {
                                "tool_actions": agent_result.get("tool_actions", []),
                                "compact_memory": self.compact_memory,
                                "next_wake_minutes": agent_result.get("sleep_minutes", 30)
                            }
                        },
                        start_to_close_timeout=timedelta(seconds=15)
                    )

                    await workflow.execute_activity(
                        update_order_run_state_activity,
                        {
                            "run_id": self.run_id,
                            "status": self.status,
                            "compact_memory": self.compact_memory,
                            "next_wake_time": self.next_wake_time.isoformat() if self.is_running else None
                        },
                        start_to_close_timeout=timedelta(seconds=15)
                    )

            # Scheduled Timer Fired
            elif not signal_received and self.is_running:
                self.status = "ACTIVE"
                agent_result = await workflow.execute_activity(
                    run_agent_step_activity,
                    {
                        "order_id": self.order_id,
                        "order_context": self.order_context,
                        "base_instruction": self.base_instruction,
                        "runtime_instructions": self.runtime_instructions,
                        "compact_memory": self.compact_memory,
                        "trigger_event": {"event_type": "scheduled_wake_up", "payload": {"reason": "Routine SLA check"}},
                        "trigger_source": "TIMER"
                    },
                    start_to_close_timeout=timedelta(seconds=45)
                )

                self.compact_memory = agent_result.get("compact_memory", self.compact_memory)
                self.sleep_duration_seconds = agent_result.get("sleep_minutes", 30) * 60
                self.next_wake_time = datetime.now() + timedelta(seconds=self.sleep_duration_seconds)
                self.status = "SLEEPING"

                await workflow.execute_activity(
                    record_activity_log_activity,
                    {
                        "run_id": self.run_id,
                        "log_type": "REASONING",
                        "trigger_source": "TIMER",
                        "title": "Scheduled Periodic Review",
                        "details": agent_result.get("thoughts", "Routine check completed."),
                        "metadata_payload": {
                            "tool_actions": agent_result.get("tool_actions", []),
                            "compact_memory": self.compact_memory,
                            "next_wake_minutes": agent_result.get("sleep_minutes", 30)
                        }
                    },
                    start_to_close_timeout=timedelta(seconds=15)
                )

                await workflow.execute_activity(
                    update_order_run_state_activity,
                    {
                        "run_id": self.run_id,
                        "status": self.status,
                        "compact_memory": self.compact_memory,
                        "next_wake_time": self.next_wake_time.isoformat()
                    },
                    start_to_close_timeout=timedelta(seconds=15)
                )

        # 4. Finalize Workflow & Generate End-of-Run Post-Mortem
        final_summary = await workflow.execute_activity(
            finalize_run_activity,
            {
                "run_id": self.run_id,
                "order_id": self.order_id,
                "order_context": self.order_context,
                "compact_memory": self.compact_memory,
                "runtime_instructions": self.runtime_instructions
            },
            start_to_close_timeout=timedelta(seconds=45)
        )

        return {
            "run_id": self.run_id,
            "order_id": self.order_id,
            "final_status": self.status,
            "final_summary": final_summary
        }


# -------------------------------------------------------------
# DIRECT AUTONOMOUS STATE MACHINE RUNNER (FAIL-SAFE & ZERO-SETUP)
# -------------------------------------------------------------
async def execute_direct_initial_assessment(
    run_id: str,
    order_id: str,
    order_context: Dict[str, Any],
    base_instruction: str,
    runtime_instructions: List[str],
    wake_up_policy: str = "balanced"
):
    """
    Direct asynchronous execution of the workflow initial assessment.
    Runs when Temporal daemon is offline or starting up, ensuring the supervisor
    immediately evaluates the order, sets SLEEPING state, schedules a wake-up timer,
    and updates the rolling compact memory.
    """
    try:
        logger.info(f"Starting direct initial assessment for run {run_id} ({order_id})...")
        # 1. Log Workflow Started
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "EVENT",
            "trigger_source": "START",
            "title": f"Order #{order_id} Workflow Started",
            "details": f"Initialized with supervisor policy '{wake_up_policy}'.",
            "metadata_payload": order_context
        })

        # 2. Run initial reasoning step with Gemini
        initial_agent_result = await run_agent_step_activity({
            "order_id": order_id,
            "order_context": order_context,
            "base_instruction": base_instruction,
            "runtime_instructions": runtime_instructions,
            "compact_memory": f"Order #{order_id} placed. Reviewing items and SLA.",
            "trigger_event": {"event_type": "order_created", "payload": order_context},
            "trigger_source": "START"
        })

        compact_mem = initial_agent_result.get("compact_memory", f"Order #{order_id} assessed.")
        sleep_mins = initial_agent_result.get("sleep_minutes", 30)
        next_wake = datetime.now() + timedelta(minutes=sleep_mins)

        # 3. Log initial assessment reasoning
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "REASONING",
            "trigger_source": "START",
            "title": "Initial Order Assessment",
            "details": initial_agent_result.get("thoughts", "Initial review complete. Order SLA within expected bounds."),
            "metadata_payload": {
                "tool_actions": initial_agent_result.get("tool_actions", []),
                "compact_memory": compact_mem,
                "next_wake_minutes": sleep_mins
            }
        })

        # 4. Update order run state to SLEEPING
        await update_order_run_state_activity({
            "run_id": run_id,
            "status": "SLEEPING",
            "compact_memory": compact_mem,
            "next_wake_time": next_wake.isoformat()
        })
        logger.info(f"Direct initial assessment completed for {run_id}. Status set to SLEEPING.")
    except Exception as e:
        logger.error(f"Error in direct initial assessment for {run_id}: {e}", exc_info=True)


async def execute_direct_event_step(
    run_id: str,
    order_id: str,
    event_type: str,
    payload: Dict[str, Any]
):
    """
    Direct asynchronous execution of event handling when Temporal daemon is offline.
    Runs Tier-1 classification, Tier-2 agent reasoning with tools, compact memory update,
    and handles terminal events.
    """
    try:
        from sqlmodel import Session, select
        from .db import engine
        from .models import OrderRun, Supervisor

        with Session(engine) as session:
            run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
            if not run:
                return
            supervisor = session.exec(select(Supervisor).where(Supervisor.id == run.supervisor_id)).first()
            base_instruction = supervisor.base_instruction if supervisor else ""
            wake_policy = supervisor.wake_up_policy if supervisor else "balanced"
            order_context = run.order_context
            compact_memory = run.compact_memory
            runtime_instructions = list(run.runtime_instructions or [])

        # 1. Log incoming signal
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "EVENT",
            "trigger_source": "SIGNAL",
            "title": f"Incoming Signal: {event_type}",
            "details": f"Payload received from simulator/external carrier: {str(payload)[:100]}",
            "metadata_payload": payload
        })

        # 2. Check for terminal events (delivered / cancelled)
        if event_type in ["delivered", "order_cancelled", "order_refunded"]:
            await update_order_run_state_activity({
                "run_id": run_id,
                "status": "COMPLETED",
                "next_wake_time": None
            })
            await record_activity_log_activity({
                "run_id": run_id,
                "log_type": "FINAL_SUMMARY",
                "trigger_source": "SIGNAL",
                "title": "Order Delivered Successfully",
                "details": "Customer delivery confirmed by carrier. Order fulfilled and workflow marked COMPLETED.",
                "metadata_payload": payload
            })
            import asyncio
            asyncio.create_task(finalize_run_activity({
                "run_id": run_id,
                "order_id": order_id,
                "order_context": order_context,
                "compact_memory": compact_memory,
                "runtime_instructions": runtime_instructions
            }))
            logger.info(f"Run {run_id} finalized with terminal event '{event_type}'. Status set to COMPLETED immediately.")
            return

        # 3. Tier-1 Event Classification
        classification = await classify_event_activity({
            "event_type": event_type,
            "payload": payload,
            "compact_memory": compact_memory,
            "wake_up_policy": wake_policy
        })

        decision = classification.get("decision", "WAKE_NOW")
        urgency = classification.get("urgency", "MEDIUM")
        class_reason = classification.get("reasoning", "")

        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "CLASSIFICATION",
            "trigger_source": "AGENT",
            "title": f"Tier-1 Decision: {decision} ({urgency} Urgency)",
            "details": class_reason,
            "metadata_payload": classification
        })

        # 4. If Tier-1 decides to wake up, execute Tier-2 agent reasoning
        if decision == "WAKE_NOW":
            await update_order_run_state_activity({
                "run_id": run_id,
                "status": "ACTIVE"
            })

            agent_result = await run_agent_step_activity({
                "order_id": order_id,
                "order_context": order_context,
                "base_instruction": base_instruction,
                "runtime_instructions": runtime_instructions,
                "compact_memory": compact_memory,
                "trigger_event": {"event_type": event_type, "payload": payload},
                "trigger_source": "SIGNAL"
            })

            updated_compact_memory = agent_result.get("compact_memory", compact_memory)
            sleep_mins = agent_result.get("sleep_minutes", 30)
            next_wake = datetime.now() + timedelta(minutes=sleep_mins)

            await record_activity_log_activity({
                "run_id": run_id,
                "log_type": "REASONING",
                "trigger_source": "SIGNAL",
                "title": f"Agent Action on '{event_type}'",
                "details": agent_result.get("thoughts", "Action taken."),
                "metadata_payload": {
                    "tool_actions": agent_result.get("tool_actions", []),
                    "compact_memory": updated_compact_memory,
                    "next_wake_minutes": sleep_mins
                }
            })

            new_status = "ESCALATED" if agent_result.get("is_escalated") else "SLEEPING"
            await update_order_run_state_activity({
                "run_id": run_id,
                "status": new_status,
                "compact_memory": updated_compact_memory,
                "next_wake_time": next_wake.isoformat()
            })
            logger.info(f"Direct event handling completed for {run_id}. New status: {new_status}")
    except Exception as e:
        logger.error(f"Error in direct event step for {run_id}: {e}", exc_info=True)


async def execute_direct_scheduled_wakeup(run_id: str, trigger_source: str = "TIMER", custom_title: str = None):
    """
    Triggered when next_wake_time has been reached or passed (e.g. overnight or timer expiry).
    Wakes the supervisor up, logs the scheduled review, executes a periodic
    status check with Gemini agent, updates compact memory, and sets the next wake-up.
    """
    try:
        from sqlmodel import Session, select
        from .db import engine
        from .models import OrderRun, Supervisor

        with Session(engine) as session:
            run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
            if not run or run.status not in ["SLEEPING", "ACTIVE"]:
                return
            supervisor = session.exec(select(Supervisor).where(Supervisor.id == run.supervisor_id)).first()
            base_instruction = supervisor.base_instruction if supervisor else ""
            wake_policy = supervisor.wake_up_policy if supervisor else "balanced"
            order_id = run.order_id
            order_context = run.order_context
            compact_memory = run.compact_memory
            runtime_instructions = list(run.runtime_instructions or [])

        # 1. Update status to ACTIVE for wake-up reasoning
        await update_order_run_state_activity({
            "run_id": run_id,
            "status": "ACTIVE"
        })

        # 2. Log Wake-Up Event
        event_title = custom_title or ("Scheduled Wake-Up: Periodic Order Review" if trigger_source == "TIMER" else "Force Wake: Manual Order Review")
        event_details = "Wake-up timer reached. Supervisor evaluating fulfillment against SLA." if trigger_source == "TIMER" else "Operator triggered manual force wake. Supervisor awakened to verify status."
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "EVENT",
            "trigger_source": trigger_source,
            "title": event_title,
            "details": event_details,
            "metadata_payload": {"order_id": order_id, "trigger": trigger_source}
        })

        # 3. Run Agent Reasoning Step
        agent_result = await run_agent_step_activity({
            "order_id": order_id,
            "order_context": order_context,
            "base_instruction": base_instruction,
            "runtime_instructions": runtime_instructions,
            "compact_memory": compact_memory,
            "trigger_event": {
                "event_type": "manual_force_wake" if trigger_source == "OPERATOR" else "scheduled_wake_up",
                "payload": {"reason": "Manual operator wake-up request" if trigger_source == "OPERATOR" else "Periodic SLA review"}
            },
            "trigger_source": trigger_source
        })

        updated_compact_memory = agent_result.get("compact_memory", compact_memory)
        sleep_mins = agent_result.get("sleep_minutes", 30)
        next_wake = datetime.now() + timedelta(minutes=sleep_mins)

        # 4. Log reasoning outcome
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "REASONING",
            "trigger_source": "TIMER",
            "title": "Periodic Review Completed",
            "details": agent_result.get("thoughts", "Periodic review complete. Order progressing normally."),
            "metadata_payload": {
                "tool_actions": agent_result.get("tool_actions", []),
                "compact_memory": updated_compact_memory,
                "next_wake_minutes": sleep_mins
            }
        })

        # 5. Set status back to SLEEPING with new future next_wake_time
        new_status = "ESCALATED" if agent_result.get("is_escalated") else "SLEEPING"
        await update_order_run_state_activity({
            "run_id": run_id,
            "status": new_status,
            "compact_memory": updated_compact_memory,
            "next_wake_time": next_wake.isoformat()
        })
        logger.info(f"Scheduled wake-up completed for {run_id}. Next wake set for {next_wake.isoformat()}")
    except Exception as e:
        logger.error(f"Error executing scheduled wake-up for {run_id}: {e}", exc_info=True)


async def execute_direct_instruction_step(run_id: str, instruction: str):
    """
    Direct execution when an operator injects a live instruction.
    Transitions status to ACTIVE, evaluates guidance, takes tool actions if required,
    updates compact memory, and transitions back to SLEEPING.
    """
    try:
        from sqlmodel import Session, select
        from .db import engine
        from .models import OrderRun, Supervisor

        with Session(engine) as session:
            run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
            if not run or run.status in ["COMPLETED", "TERMINATED"]:
                return
            supervisor = session.exec(select(Supervisor).where(Supervisor.id == run.supervisor_id)).first()
            base_instruction = supervisor.base_instruction if supervisor else ""
            wake_policy = supervisor.wake_up_policy if supervisor else "balanced"
            order_id = run.order_id
            order_context = run.order_context
            compact_memory = run.compact_memory
            runtime_instructions = list(run.runtime_instructions or [])

        # 1. Transition to ACTIVE while evaluating operator guidance
        await update_order_run_state_activity({
            "run_id": run_id,
            "status": "ACTIVE"
        })

        # 2. Run agent reasoning with the new instruction
        agent_result = await run_agent_step_activity({
            "order_id": order_id,
            "order_context": order_context,
            "base_instruction": base_instruction,
            "runtime_instructions": runtime_instructions,
            "compact_memory": compact_memory,
            "trigger_event": {
                "event_type": "operator_guidance",
                "payload": {"guidance": instruction}
            },
            "trigger_source": "OPERATOR"
        })

        updated_compact_memory = agent_result.get("compact_memory", compact_memory)
        sleep_mins = agent_result.get("sleep_minutes", 30)
        next_wake = datetime.now() + timedelta(minutes=sleep_mins)

        # 3. Log reasoning outcome
        await record_activity_log_activity({
            "run_id": run_id,
            "log_type": "REASONING",
            "trigger_source": "OPERATOR",
            "title": "Agent Evaluated Operator Guidance",
            "details": agent_result.get("thoughts", f"Operator instruction integrated: {instruction}"),
            "metadata_payload": {
                "tool_actions": agent_result.get("tool_actions", []),
                "compact_memory": updated_compact_memory,
                "next_wake_minutes": sleep_mins
            }
        })

        # 4. Check if operator instruction terminated the order (e.g. cancellation)
        if agent_result.get("is_terminal"):
            await update_order_run_state_activity({
                "run_id": run_id,
                "status": "COMPLETED",
                "compact_memory": updated_compact_memory,
                "next_wake_time": None
            })
            await record_activity_log_activity({
                "run_id": run_id,
                "log_type": "FINAL_SUMMARY",
                "trigger_source": "OPERATOR",
                "title": "Order Closed per Operator Instruction",
                "details": f"Operator instruction closed workflow: '{instruction}'. Outcome: {agent_result.get('terminal_outcome', 'CANCELLED')}.",
                "metadata_payload": {"instruction": instruction, "outcome": agent_result.get("terminal_outcome")}
            })
            import asyncio
            asyncio.create_task(finalize_run_activity({
                "run_id": run_id,
                "order_id": order_id,
                "order_context": order_context,
                "compact_memory": updated_compact_memory,
                "runtime_instructions": runtime_instructions
            }))
            logger.info(f"Operator instruction closed workflow {run_id}.")
            return

        new_status = "ESCALATED" if agent_result.get("is_escalated") else "SLEEPING"
        await update_order_run_state_activity({
            "run_id": run_id,
            "status": new_status,
            "compact_memory": updated_compact_memory,
            "next_wake_time": next_wake.isoformat()
        })
        logger.info(f"Operator instruction evaluated for {run_id}. Status set to: {new_status}")
    except Exception as e:
        logger.error(f"Error in direct instruction step for {run_id}: {e}", exc_info=True)
