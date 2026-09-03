import re
import json
import logging
from typing import Dict, Any, List
from .config import settings

logger = logging.getLogger(__name__)

def clean_plain_text(val: Any) -> Any:
    """Removes markdown syntax like **, *, __, `#`, etc. ensuring clean, professional text."""
    if isinstance(val, str):
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", val)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        text = re.sub(r"__([^_]+)__", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"#+\s*", "", text)
        text = text.replace("**", "").replace("*", "")
        return re.sub(r"\s+", " ", text).strip()
    elif isinstance(val, list):
        return [clean_plain_text(item) for item in val]
    elif isinstance(val, dict):
        return {k: clean_plain_text(v) for k, v in val.items()}
    return val

def safe_extract_json(raw_text: str) -> Any:
    """Extracts JSON from response text even if wrapped in markdown codeblocks."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


# -------------------------------------------------------------
# 1. TOOL DEFINITIONS & SIMULATED EXECUTIONS
# -------------------------------------------------------------
TOOL_DEFINITIONS = [
    {
        "name": "message_fulfillment_team",
        "description": "Send an operational message to warehouse/fulfillment for priority packing, stock hold, or order inspection.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "urgency": {"type": "STRING", "description": "Urgency level: LOW, MEDIUM, HIGH, CRITICAL"},
                "message": {"type": "STRING", "description": "Instruction or update for warehouse operators"},
                "action_required": {"type": "STRING", "description": "Expected action, e.g. Expedite packing, Hold shipment"}
            },
            "required": ["urgency", "message", "action_required"]
        }
    },
    {
        "name": "message_payments_team",
        "description": "Alert finance or payments team regarding payment failure, refund request, fraud review, or retry validation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reason": {"type": "STRING", "description": "Reason for contacting payments team"},
                "amount": {"type": "NUMBER", "description": "Transaction amount"},
                "action": {"type": "STRING", "description": "Action: 'refund', 'retry', 'investigate', 'credit'"}
            },
            "required": ["reason", "amount", "action"]
        }
    },
    {
        "name": "message_logistics_team",
        "description": "Contact carrier/logistics regarding delayed shipments, route tracking, or customs clearance.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "carrier": {"type": "STRING", "description": "Carrier name, e.g. FedEx, BlueDart, DHL, UPS"},
                "issue_type": {"type": "STRING", "description": "Type of issue: DELAY, LOST_IN_TRANSIT, ADDRESS_INCOMPLETE, WEATHER_HOLD"},
                "inquiry_details": {"type": "STRING", "description": "Detailed explanation of inquiry"}
            },
            "required": ["carrier", "issue_type", "inquiry_details"]
        }
    },
    {
        "name": "message_customer",
        "description": "Send a proactive, empathetic message or update to customer via email or SMS.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "channel": {"type": "STRING", "description": "Channel: 'email' or 'sms'"},
                "message_body": {"type": "STRING", "description": "Message text delivered to customer"},
                "sentiment_tone": {"type": "STRING", "description": "Tone: 'informative', 'apologetic', 'reassuring', 'urgent'"}
            },
            "required": ["channel", "message_body", "sentiment_tone"]
        }
    },
    {
        "name": "create_internal_note",
        "description": "Record an internal operational audit note or observation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "note_type": {"type": "STRING", "description": "Category: 'observation', 'risk_flag', 'sla_warning', 'decision_rationale'"},
                "content": {"type": "STRING", "description": "Internal note content"}
            },
            "required": ["note_type", "content"]
        }
    },
    {
        "name": "schedule_next_wake_up",
        "description": "Set the timer for when supervisor workflow should wake up next.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "duration_minutes": {"type": "INTEGER", "description": "Minutes to sleep before next scheduled wake-up (e.g. 15, 30, 60)"},
                "wake_up_reason": {"type": "STRING", "description": "What to inspect when waking up"}
            },
            "required": ["duration_minutes", "wake_up_reason"]
        }
    },
    {
        "name": "update_memory_summary",
        "description": "Refresh and compact the rolling memory summary with latest events, decisions, and current state.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "new_summary": {"type": "STRING", "description": "Updated chronological summary of order journey and state"}
            },
            "required": ["new_summary"]
        }
    },
    {
        "name": "escalate_issue",
        "description": "Escalate order to human operations for unresolvable exceptions or critical SLA breaches.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "department": {"type": "STRING", "description": "Target team, e.g. 'Human Operations Lead', 'Fraud Security'"},
                "severity": {"type": "STRING", "description": "Severity: 'MEDIUM', 'HIGH', 'CRITICAL'"},
                "reason": {"type": "STRING", "description": "Why human intervention is required"}
            },
            "required": ["department", "severity", "reason"]
        }
    },
    {
        "name": "close_workflow",
        "description": "Recommend closing supervisor workflow when order reaches terminal state (Delivered, Refunded, Cancelled).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "reason": {"type": "STRING", "description": "Why order is complete"},
                "outcome": {"type": "STRING", "description": "Final outcome: 'SUCCESSFUL_DELIVERY', 'REFUNDED_COMPLETE', 'CANCELLED'"}
            },
            "required": ["reason", "outcome"]
        }
    }
]

def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Simulates tool execution and returns a structured record for database activity log."""
    if tool_name == "message_fulfillment_team":
        return {
            "status": "SUCCESS", "action": "message_fulfillment_team",
            "details": f"Dispatched {args.get('urgency')} alert to warehouse: {args.get('message')}. Action: {args.get('action_required')}",
            "args": args
        }
    elif tool_name == "message_payments_team":
        return {
            "status": "SUCCESS", "action": "message_payments_team",
            "details": f"Payment team ticket created for amount . Action: {args.get('action')}. Reason: {args.get('reason')}",
            "args": args
        }
    elif tool_name == "message_logistics_team":
        return {
            "status": "SUCCESS", "action": "message_logistics_team",
            "details": f"Logistics inquiry sent to {args.get('carrier')} for issue: {args.get('issue_type')}. Details: {args.get('inquiry_details')}",
            "args": args
        }
    elif tool_name == "message_customer":
        return {
            "status": "SUCCESS", "action": "message_customer",
            "details": f"Sent {args.get('sentiment_tone')} {args.get('channel')} to customer: '{args.get('message_body')}'",
            "args": args
        }
    elif tool_name == "create_internal_note":
        return {
            "status": "SUCCESS", "action": "create_internal_note",
            "details": f"Internal note ({args.get('note_type')}): {args.get('content')}",
            "args": args
        }
    elif tool_name == "schedule_next_wake_up":
        return {
            "status": "SUCCESS", "action": "schedule_next_wake_up",
            "duration_minutes": args.get("duration_minutes", 30),
            "wake_up_reason": args.get("wake_up_reason", "Scheduled progress review"),
            "details": f"Next wake-up scheduled in {args.get('duration_minutes', 30)} minutes for: {args.get('wake_up_reason')}"
        }
    elif tool_name == "update_memory_summary":
        return {
            "status": "SUCCESS", "action": "update_memory_summary",
            "new_summary": args.get("new_summary", ""),
            "details": "Compact memory summary updated."
        }
    elif tool_name == "escalate_issue":
        return {
            "status": "ESCALATED", "action": "escalate_issue",
            "department": args.get("department"), "severity": args.get("severity"),
            "details": f"Order escalated to {args.get('department')} with {args.get('severity')} severity: {args.get('reason')}",
            "args": args
        }
    elif tool_name == "close_workflow":
        return {
            "status": "TERMINAL_RECOMMENDED", "action": "close_workflow",
            "outcome": args.get("outcome"),
            "details": f"Supervisor recommended closure ({args.get('outcome')}): {args.get('reason')}",
            "args": args
        }
    else:
        return {"status": "UNKNOWN_TOOL", "action": tool_name, "details": f"Tool '{tool_name}' executed with args: {args}"}

# -------------------------------------------------------------
# 2. TIER-1 LIGHTWEIGHT CLASSIFIER (Gemini 3.7 Flash)
# -------------------------------------------------------------
DEFAULT_URGENT_EVENTS = {
    "payment_failed", "shipment_delayed", "customer_message_received",
    "refund_requested", "delivered", "order_created"
}

def classify_event(event_type: str, payload: Dict[str, Any], compact_memory: str, wake_up_policy: str = "balanced") -> Dict[str, Any]:
    """Tier-1: Evaluates whether incoming event requires immediate agent wake-up or can be silently logged."""
    prompt = f"""You are a Tier-1 Event Classifier for an AI Order Supervisor.
Decide whether this incoming event requires immediate agent wake-up (WAKE_NOW) or if the system should stay asleep until scheduled timer (REMAIN_ASLEEP).

CURRENT COMPACT MEMORY:
{compact_memory}

SUPERVISOR POLICY: {wake_up_policy.upper()}

INCOMING EVENT:
- Type: {event_type}
- Payload: {json.dumps(payload, default=str)}

Respond with JSON:
{{
  "decision": "WAKE_NOW" or "REMAIN_ASLEEP",
  "urgency": "LOW", "MEDIUM", "HIGH", or "CRITICAL",
  "reasoning": "1-2 sentence explanation (PLAIN TEXT ONLY, NO ASTERISKS ** OR MARKDOWN)"
}}
"""
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            models_to_try = [settings.GEMINI_MODEL or "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.5-flash"]
            response = None
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    if response:
                        break
                except Exception as ex:
                    logger.warning(f"Model {model_name} unavailable ({ex}), trying fallback...")
            parsed = clean_plain_text(safe_extract_json(response.text)) if response and response.text else {}
            return {
                "decision": parsed.get("decision", "WAKE_NOW"),
                "urgency": parsed.get("urgency", "MEDIUM"),
                "reasoning": parsed.get("reasoning", f"Classified via {model_name}.")
            }
        except Exception as e:
            logger.warning(f"Gemini classifier fallback: {e}")
            
    if wake_up_policy == "aggressive" or event_type in DEFAULT_URGENT_EVENTS:
        return {
            "decision": "WAKE_NOW",
            "urgency": "HIGH" if event_type in ["payment_failed", "refund_requested", "shipment_delayed"] else "MEDIUM",
            "reasoning": f"Event '{event_type}' requires immediate supervisor evaluation according to operational policy."
        }
    else:
        return {
            "decision": "REMAIN_ASLEEP",
            "urgency": "LOW",
            "reasoning": f"Routine event '{event_type}' logged into timeline. Workflow will remain asleep until next timer."
        }

# -------------------------------------------------------------
# 3. TIER-2 MAIN SUPERVISOR AGENT (Gemini 3.7 Flash)
# -------------------------------------------------------------
def run_agent_reasoning_step(
    order_id: str,
    order_context: Dict[str, Any],
    base_instruction: str,
    runtime_instructions: List[str],
    compact_memory: str,
    trigger_event: Dict[str, Any],
    trigger_source: str = "SIGNAL"
) -> Dict[str, Any]:
    """
    Tier-2 Main Supervisor Agent reasoning step.
    Uses Google Gemini structured JSON mode matching autograde_service.py pattern.
    Executes in a single high-speed inference call, eliminating AFC loops and multi-turn timeouts.
    """
    tools_summary = """
AVAILABLE TOOLS:
1. message_customer(channel, subject, message) - Inform/reassure customer regarding order status or delays.
2. message_logistics_team(carrier, issue_type, inquiry_details) - Contact carrier to expedite or reroute shipment.
3. message_fulfillment_team(urgency, message, action_required) - Tell warehouse to hold, inspect, or expedite package.
4. message_payments_team(reason, amount, action) - Alert finance regarding payment failure, refund, or investigation.
5. create_internal_note(note_type, content) - Log internal audit note or risk flag.
6. update_memory_summary(new_summary) - Keep rolling context compact and updated.
7. schedule_next_wake_up(duration_minutes, wake_up_reason) - Set sleep duration (e.g. 15, 30, 60 mins).
8. close_workflow(outcome, summary) - Conclude workflow upon terminal delivery or cancellation.
"""

    prompt = f"""{base_instruction}

ORDER ID: {order_id}
ORDER CONTEXT:
{json.dumps(order_context, indent=2, default=str)}

RUNTIME OPERATOR DIRECTIVES:
{json.dumps(runtime_instructions, indent=2) if runtime_instructions else "None"}

CURRENT COMPACT MEMORY SUMMARY:
{compact_memory}

TRIGGER EVENT:
Source: {trigger_source}
Details: {json.dumps(trigger_event, indent=2, default=str)}

{tools_summary}

YOUR TASK:
1. Analyze the triggering event and current situation for order {order_id}.
2. If this is an operator cancellation directive, mark is_terminal=true, call 'close_workflow' with outcome='CANCELLED_BY_OPERATOR', and alert customer/warehouse.
3. If this is a shipment delay or issue, call 'message_logistics_team' and 'message_customer', and flag is_escalated=true.
4. Always provide an updated 2-3 sentence 'new_compact_memory' summarizing latest progress.
5. Set 'sleep_minutes' (default 30) for when to check order next.
6. Return a valid JSON object ONLY. Do NOT include any markdown formatting or asterisks.

REQUIRED JSON OUTPUT SCHEMA:
{{
  "thoughts": "1-2 sentence plain text reasoning (NO ASTERISKS **)",
  "tool_actions": [
    {{"action": "tool_name", "args": {{"param_key": "param_value"}}}}
  ],
  "new_compact_memory": "Updated 2-3 sentence rolling memory summary (clean plain text)",
  "sleep_minutes": 30,
  "is_terminal": false,
  "is_escalated": false
}}
"""

    tool_actions_taken = []
    thoughts = ""
    new_compact_memory = compact_memory
    sleep_minutes = 30
    is_terminal = False
    terminal_outcome = None
    is_escalated = False

    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            models_to_try = [settings.GEMINI_MODEL or "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.5-flash"]
            
            parsed = None
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    if response and response.text:
                        parsed = safe_extract_json(response.text)
                        if parsed and isinstance(parsed, dict):
                            break
                except Exception as ex:
                    logger.warning(f"Model {m} failed ({ex}), trying next model...")

            if parsed and isinstance(parsed, dict):
                thoughts = clean_plain_text(parsed.get("thoughts", f"Evaluated trigger {trigger_source}."))
                new_compact_memory = clean_plain_text(parsed.get("new_compact_memory", compact_memory))
                sleep_minutes = int(parsed.get("sleep_minutes", 30))
                is_terminal = bool(parsed.get("is_terminal", False))
                is_escalated = bool(parsed.get("is_escalated", False))

                # Execute all recommended tools
                for item in parsed.get("tool_actions", []):
                    action_name = item.get("action")
                    action_args = item.get("args", {})
                    if action_name in [t["name"] for t in TOOL_DEFINITIONS]:
                        exec_res = execute_tool(action_name, action_args)
                        tool_actions_taken.append(exec_res)
                        if action_name == "close_workflow":
                            is_terminal = True
                            terminal_outcome = action_args.get("outcome", "COMPLETED")
                        elif action_name == "escalate_issue":
                            is_escalated = True

        except Exception as e:
            logger.error(f"Gemini structured JSON reasoning error: {e}")
            thoughts = f"Agent evaluated trigger '{trigger_event.get('event_type', trigger_source)}'."

    # Deterministic resilient fallback if tools were not called
    if not tool_actions_taken:
        event_type = trigger_event.get("event_type", trigger_source)
        if event_type == "shipment_delayed":
            tool_actions_taken.append(execute_tool("message_customer", {
                "channel": "email",
                "message": f"Dear Customer, your order #{order_id} is experiencing a brief carrier delay. We are actively expediting delivery with the carrier."
            }))
            tool_actions_taken.append(execute_tool("message_logistics_team", {
                "carrier": trigger_event.get("payload", {}).get("carrier", "FedEx"),
                "issue_type": "DELAY",
                "inquiry_details": "Requesting priority routing for delayed parcel."
            }))
            new_compact_memory = f"Shipment delayed for #{order_id}. Customer notified and logistics escalated. Awaiting carrier update."
            is_escalated = True
        elif event_type in ["payment_failed"]:
            tool_actions_taken.append(execute_tool("message_customer", {
                "channel": "email",
                "message": f"Payment verification pending for #{order_id}. Please update payment method to avoid dispatch hold."
            }))
            new_compact_memory = f"Payment verification pending for #{order_id}. Customer notified to retry payment."
            is_escalated = True
        elif event_type == "operator_guidance":
            guidance = trigger_event.get("payload", {}).get("guidance", "")
            if any(w in guidance.lower() for w in ["cancel", "abort", "refund"]):
                tool_actions_taken.append(execute_tool("close_workflow", {
                    "outcome": "CANCELLED_BY_OPERATOR",
                    "summary": f"Order cancelled per operator directive: {guidance}"
                }))
                tool_actions_taken.append(execute_tool("message_customer", {
                    "channel": "email",
                    "message": f"Your order #{order_id} has been cancelled per request. A refund has been processed."
                }))
                new_compact_memory = f"Order #{order_id} cancelled by operator directive. Refund initiated."
                is_terminal = True
            else:
                tool_actions_taken.append(execute_tool("message_logistics_team", {
                    "carrier": "FedEx",
                    "issue_type": "PRIORITY_UPGRADE",
                    "inquiry_details": f"Operator directive: {guidance}"
                }))
                new_compact_memory = f"Operator directive applied: {guidance}. Logistics notified to expedite."

    return {
        "thoughts": clean_plain_text(thoughts),
        "tool_actions": tool_actions_taken,
        "compact_memory": clean_plain_text(new_compact_memory),
        "sleep_minutes": sleep_minutes,
        "wake_up_reason": "Periodic review",
        "is_terminal": is_terminal,
        "terminal_outcome": terminal_outcome,
        "is_escalated": is_escalated
    }

def generate_final_learnings(
    order_id: str,
    order_context: Dict[str, Any],
    compact_memory: str,
    activity_history: List[Dict[str, Any]],
    runtime_instructions: List[str]
) -> Dict[str, Any]:
    """Generates post-mortem report and recommendations when workflow finishes."""
    prompt = f"""You are an Order Operations Reviewer. Generate a final report for Order ID {order_id}.

ORDER CONTEXT:
{json.dumps(order_context, indent=2, default=str)}

ROLLING COMPACT MEMORY:
{compact_memory}

OPERATOR INSTRUCTIONS:
{json.dumps(runtime_instructions, indent=2)}

Generate a JSON object with:
- "final_summary": "A 2-3 sentence overview of the order lifecycle"
- "important_actions_taken": ["List of 3-5 major actions executed by supervisor"]
- "key_learnings": ["2-3 operational learnings observed during this run"]
- "recommendations": ["2-3 actionable recommendations to improve SLA and customer satisfaction"]
"""
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            models_to_try = [settings.GEMINI_MODEL or "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.5-flash"]
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2
                        )
                    )
                    if response:
                        return clean_plain_text(safe_extract_json(response.text))
                except Exception as ex:
                    logger.warning(f"Final learnings model {m} failed ({ex}), trying fallback...")
        except Exception as e:
            logger.warning(f"Gemini final summary error: {e}")
            
    return {
        "final_summary": f"Order #{order_id} completed its lifecycle with proactive AI supervision across all fulfillment stages.",
        "important_actions_taken": [
            f"Supervised order #{order_id} from initial confirmation to terminal state.",
            "Monitored carrier transit times and handled real-time updates.",
            "Maintained continuous customer and internal stakeholder alignment."
        ],
        "key_learnings": [
            "Early carrier delay detection significantly mitigates customer friction.",
            "Rolling memory compaction preserved context while maintaining high token efficiency."
        ],
        "recommendations": [
            "Enable automated pre-alerting for carriers on high-value orders.",
            "Incorporate dynamic customer SMS notifications alongside email."
        ]
    }
