import json
import logging
from typing import Dict, Any, List
from .config import settings

logger = logging.getLogger(__name__)

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
  "reasoning": "1-2 sentence explanation"
}}
"""
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model_name = settings.GEMINI_MODEL or "gemini-3.7-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            parsed = json.loads(response.text)
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
    """Tier-2 Main Supervisor Agent reasoning step with multi-turn tool calling."""
    system_instruction = f"""{base_instruction}

ORDER ID: {order_id}
ORDER CONTEXT:
{json.dumps(order_context, indent=2, default=str)}

RUNTIME OPERATOR INSTRUCTIONS:
{json.dumps(runtime_instructions, indent=2) if runtime_instructions else "None"}

COMPACT MEMORY SUMMARY:
{compact_memory}

TRIGGER FOR THIS STEP:
Source: {trigger_source}
Details: {json.dumps(trigger_event, indent=2, default=str)}

YOUR TASK:
1. Analyze the triggering event and current situation.
2. Call appropriate business tools (message customer, fulfillment, logistics, internal note) if action is required.
3. Always update the compact memory summary using 'update_memory_summary'.
4. If order is NOT complete, call 'schedule_next_wake_up'.
5. If order is delivered or terminal, call 'close_workflow'.
"""

    tool_actions_taken = []
    thoughts = ""
    new_compact_memory = compact_memory
    sleep_minutes = 30
    wake_up_reason = "Periodic supervisor review"
    is_terminal = False
    terminal_outcome = None
    is_escalated = False

    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model_name = settings.GEMINI_MODEL or "gemini-3.7-flash"
            gemini_tools = []
            for t in TOOL_DEFINITIONS:
                gemini_tools.append(types.Tool(function_declarations=[
                    types.FunctionDeclaration(
                        name=t["name"],
                        description=t["description"],
                        parameters=types.Schema(
                            type=t["parameters"]["type"],
                            properties={
                                k: types.Schema(type=v["type"], description=v.get("description", ""))
                                for k, v in t["parameters"]["properties"].items()
                            },
                            required=t["parameters"].get("required", [])
                        )
                    )
                ]))
            
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    tools=gemini_tools
                )
            )
            
            response = chat.send_message(f"Evaluate situation for order {order_id}. Take necessary tool actions and update memory summary.")
            
            iterations = 0
            while iterations < 5:
                iterations += 1
                if response.text:
                    thoughts += response.text + "\n"
                    
                function_calls = []
                for candidate in response.candidates:
                    for part in candidate.content.parts:
                        if part.function_call:
                            function_calls.append(part.function_call)
                            
                if not function_calls:
                    break
                    
                tool_responses = []
                for call in function_calls:
                    tool_name = call.name
                    args = dict(call.args) if call.args else {}
                    exec_result = execute_tool(tool_name, args)
                    tool_actions_taken.append(exec_result)
                    
                    if tool_name == "update_memory_summary":
                        new_compact_memory = args.get("new_summary", new_compact_memory)
                    elif tool_name == "schedule_next_wake_up":
                        sleep_minutes = args.get("duration_minutes", 30)
                        wake_up_reason = args.get("wake_up_reason", wake_up_reason)
                    elif tool_name == "close_workflow":
                        is_terminal = True
                        terminal_outcome = args.get("outcome", "COMPLETED")
                    elif tool_name == "escalate_issue":
                        is_escalated = True
                        
                    tool_responses.append(types.Part.from_function_response(
                        name=tool_name,
                        response={"result": exec_result}
                    ))
                    
                response = chat.send_message(tool_responses)
                
        except Exception as e:
            logger.error(f"Gemini agent inference error: {e}")
            thoughts = f"Agent evaluated trigger '{trigger_event.get('event_type', trigger_source)}'."

    # Fallback tool actions
    if not tool_actions_taken:
        event_type = trigger_event.get("event_type", trigger_source)
        if event_type == "shipment_delayed":
            tool_actions_taken.append(execute_tool("message_customer", {
                "channel": "email",
                "message_body": f"Dear Customer, your order #{order_id} is experiencing a brief carrier delay. We are actively expediting delivery.",
                "sentiment_tone": "apologetic"
            }))
            tool_actions_taken.append(execute_tool("message_logistics_team", {
                "carrier": trigger_event.get("payload", {}).get("carrier", "FedEx"),
                "issue_type": "DELAY",
                "inquiry_details": "Requesting priority routing for delayed parcel."
            }))
            new_compact_memory = f"Shipment delayed for #{order_id}. Customer notified via email and logistics escalated. Awaiting carrier update."
            sleep_minutes = 60
        elif event_type == "payment_failed":
            tool_actions_taken.append(execute_tool("message_payments_team", {
                "reason": "Payment transaction failed at gateway.",
                "amount": order_context.get("items", [{}])[0].get("price", 100.0),
                "action": "retry"
            }))
            tool_actions_taken.append(execute_tool("message_customer", {
                "channel": "email",
                "message_body": f"We encountered an issue processing payment for order #{order_id}. Please update your payment method.",
                "sentiment_tone": "urgent"
            }))
            new_compact_memory = f"Payment failure detected for order #{order_id}. Payments team alerted and customer notified."
            sleep_minutes = 30
        elif event_type in ["delivered", "order_delivered"]:
            tool_actions_taken.append(execute_tool("close_workflow", {
                "reason": "Order delivery confirmed by carrier.",
                "outcome": "SUCCESSFUL_DELIVERY"
            }))
            is_terminal = True
            terminal_outcome = "SUCCESSFUL_DELIVERY"
            new_compact_memory = f"Order #{order_id} has been successfully delivered and verified."
        else:
            tool_actions_taken.append(execute_tool("create_internal_note", {
                "note_type": "observation",
                "content": f"Order #{order_id} reviewed on trigger '{event_type}'. All parameters normal."
            }))
            new_compact_memory = f"Order #{order_id} assessed on {event_type}. Monitoring lifecycle status."
            sleep_minutes = 45

    return {
        "thoughts": thoughts.strip(),
        "tool_actions": tool_actions_taken,
        "compact_memory": new_compact_memory,
        "sleep_minutes": sleep_minutes,
        "wake_up_reason": wake_up_reason,
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
            model_name = settings.GEMINI_MODEL or "gemini-3.7-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
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
