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
            timestamp=datetime.utcnow()
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
            run.updated_at = datetime.utcnow()
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
            timestamp=datetime.utcnow()
        )
        session.add(summary_log)
        
        run = session.exec(select(OrderRun).where(OrderRun.id == run_id)).first()
        if run:
            run.status = "COMPLETED"
            run.final_summary = final_report
            run.updated_at = datetime.utcnow()
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
        if action == "pause":
            self.is_paused = True
            self.status = "PAUSED"
        elif action == "resume":
            self.is_paused = False
            self.status = "ACTIVE"
        elif action == "terminate":
            self.is_terminated = True
            self.is_running = False
            self.status = "TERMINATED"
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
        self.next_wake_time = datetime.now(timezone.utc) + timedelta(seconds=self.sleep_duration_seconds)
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

            now = datetime.now(timezone.utc)
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
                    self.next_wake_time = datetime.now(timezone.utc) + timedelta(seconds=self.sleep_duration_seconds)
                    
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
                self.next_wake_time = datetime.now(timezone.utc) + timedelta(seconds=self.sleep_duration_seconds)
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
