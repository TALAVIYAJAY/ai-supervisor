# Order Supervisor: Autonomous Long-Running AI Workflow POC
### Comprehensive Technical Specification, System Design & Implementation Guide

---

## 1. Executive Summary & Problem Statement

Modern e-commerce and order fulfillment operations involve multi-day lifecycles where exceptions (payment failures, shipping delays, customer inquiries, supplier backorders) occur unpredictably. Traditional automation relies on static, brittle rule engines or expensive, continuously polling microservices.

**Order Supervisor** is a Proof of Concept (POC) for an **autonomous, long-running AI supervisor** that oversees an individual order from initial placement to terminal completion.

### Key Architectural Principles:
1. **One Workflow per Order**: Each order is backed by an independent, durable **Temporal Workflow** that lives for minutes, hours, or days without consuming idle CPU cycles.
2. **Tri-Triggered Wake/Sleep Model**: The AI does **not** poll in a tight loop. It sleeps and executes reasoning only on:
   - **Trigger 1**: Workflow Start (Initial order assessment).
   - **Trigger 2**: High-Priority Signal/Event (Filtered by a lightweight classifier).
   - **Trigger 3**: Scheduled Wake-up Timer (e.g. periodic check-ins, SLA timeouts).
3. **2-Tier Intelligent Event Handling**:
   - **Tier 1 (Lightweight Classifier / Policy)**: Cheap, sub-second evaluation of incoming events to determine if immediate agent wake-up is required or if the event can simply be logged while remaining asleep.
   - **Tier 2 (Main Supervisor Agent)**: Full LLM reasoning with tool execution, maintaining a rolling compact memory and updating the timeline.
4. **Mocked Business Actions & Activity Persistence**: Simulated tools (message_customer, message_logistics_team, message_fulfillment_team, message_payments_team, create_internal_note) that record state changes directly to the database.
5. **Interactive Operator Dashboard & Simulator**: Next.js App Router frontend with real-time timeline visualization, event simulator panel, live run-specific instruction injection, and workflow lifecycle controls.
6. **Post-Mortem & Learnings Generation**: Automated extraction of key learnings, summary, and process recommendations upon order completion.

---

## 2. Technology Stack & Rationale

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Workflow Engine** | **Temporal Python SDK (	emporalio)** | Provides resilient, durable execution, distributed timers, signal handlers, and deterministic replayability. |
| **Backend API** | **FastAPI (Python 3.11+)** | High-performance asynchronous API framework with native OpenAPI schema generation and seamless async Temporal client integration. |
| **LLM & Agent Runtime** | **Google Gemini 3.7 Flash (google-genai)** | Ultra-fast inference (< 1s), free tier via AI Studio, native function/tool calling, and robust structured JSON outputs. |
| **Database & ORM** | **SQLite with SQLModel (SQLAlchemy 2.0 + Pydantic)** | Zero-config, ACID-compliant local database that easily scales to PostgreSQL/Supabase with zero code changes. |
| **Frontend Framework** | **Next.js 15 (App Router)** | Modern React server/client components, robust routing, and clean component modularity. |
| **UI & Styling** | **Tailwind CSS + Lucide Icons** | Clean, responsive developer dashboard matching modern SaaS aesthetics. |

---

## 3. High-Level Architecture & Data Flow

`mermaid
flowchart TD
    subgraph Frontend["Next.js 15 Frontend (App Router)"]
        UI_Dash["Dashboard & Run List"]
        UI_Inspector["Run Inspector & Timeline"]
        UI_Sim["Event Simulator Panel"]
        UI_Control["Live Instruction & Lifecycle Controls"]
    end

    subgraph Backend["FastAPI Backend Layer"]
        API_Runs["/api/runs (Create, List, Details)"]
        API_Events["/api/runs/{id}/events (Signal Trigger)"]
        API_Instruct["/api/runs/{id}/instructions"]
        API_Controls["/api/runs/{id}/[interrupt|resume|terminate]"]
        DB[(SQLite / PostgreSQL Database)]
    end

    subgraph Temporal_Cluster["Temporal Orchestration Engine"]
        WF["OrderSupervisorWorkflow\n(Durable State Machine & Timers)"]
    end

    subgraph Worker_Runtime["Temporal Python Worker & Activities"]
        Act_Classify["Activity: Event Classifier\n(Tier 1: Gemini 3.7 Flash)"]
        Act_Agent["Activity: Main Agent Reasoning & Tools\n(Tier 2: Gemini 3.7 Flash)"]
        Act_Finalize["Activity: Generate Final Summary & Learnings"]
        Act_Log["Activity: DB Persistence & Activity Logging"]
    end

    %% Interactions
    UI_Dash --> API_Runs
    UI_Inspector --> API_Runs
    UI_Sim --> API_Events
    UI_Control --> API_Instruct
    UI_Control --> API_Controls

    API_Runs --> DB
    API_Runs -- "temporal_client.start_workflow()" --> WF
    API_Events -- "workflow_handle.signal('event_signal')" --> WF
    API_Instruct -- "workflow_handle.signal('instruction_signal')" --> WF
    API_Controls -- "workflow_handle.signal('control_signal')" --> WF

    WF -- "Execute" --> Act_Classify
    WF -- "Execute" --> Act_Agent
    WF -- "Execute" --> Act_Finalize
    Act_Agent -- "Write Log & Update State" --> DB
    Act_Classify -- "Write Log" --> DB
    Act_Finalize -- "Write Final Learnings" --> DB
`

---

## 4. System Components Deep Dive

### 4.1. The Long-Running Order Workflow (OrderSupervisorWorkflow)
- **Workflow ID**: order-supervisor-<order_id>
- **Workflow State Variables**:
  - order_id: Unique identifier for the order.
  - status: ACTIVE, SLEEPING, ESCALATED, COMPLETED, TERMINATED, PAUSED.
  - compact_memory: Rolling summarized history of events, agent decisions, and outstanding action items.
  - 
ext_wake_time: ISO timestamp for the next scheduled review.
  - 
untime_instructions: List of dynamic operator instructions injected mid-flight.
  - pending_events: Queue of unprocessed signals.
- **Workflow Loop**:
  `python
  while not is_terminal_state:
      # Wait until timer expires OR a signal arrives OR workflow is paused/terminated
      await workflow.wait_condition(
          lambda: len(pending_events) > 0 or len(pending_instructions) > 0 or timer_fired or is_terminated,
          timeout=calculated_sleep_seconds
      )
      # Process triggers through 2-Tier Classifier and Main Agent
  `

### 4.2. Event-Driven Wake/Sleep (2-Tier Agent System)

`mermaid
sequenceDiagram
    autonumber
    actor Simulator as Operator / Simulator
    participant API as FastAPI Backend
    participant WF as Temporal Workflow
    participant Classify as Tier-1 Classifier Activity
    participant Agent as Tier-2 Agent Activity
    participant DB as SQLite DB

    Simulator->>API: POST /api/runs/{id}/events (e.g. shipment_delayed)
    API->>WF: Send Temporal Signal ('event_signal')
    WF->>Classify: Execute classify_event_activity(event, compact_memory)
    Note over Classify: Gemini 3.7 Flash checks urgency & sensitivity
    Classify-->>WF: Decision: WAKE_NOW (Urgent) / REMAIN_ASLEEP (Routine)
    
    alt Decision == WAKE_NOW
        WF->>Agent: Execute run_agent_step_activity(event, memory, tools)
        Note over Agent: Agent reasons & calls tools:<br/>message_customer(), message_logistics_team()
        Agent-->>WF: Tool results + New Compact Memory + Next Wake-up Duration
        WF->>DB: Log Actions & Update Status
    else Decision == REMAIN_ASLEEP
        WF->>DB: Log Event into Timeline (Silent)
        Note over WF: Workflow continues sleeping until scheduled timer
    end
`

### 4.3. Business & Runtime Tools Specification

The supervisor agent has access to 5 business action tools and 3 runtime control tools:

#### Business Actions (Mocked with DB Activity Logging):
1. **message_fulfillment_team**:
   - *Parameters*: urgency: str, message: str, ction_required: str
   - *Purpose*: Alerts warehouse staff for expedited packing, stock verification, or cancellation hold.
2. **message_payments_team**:
   - *Parameters*: 
eason: str, mount: float, ction: 'refund' | 'verify' | 'retry'
   - *Purpose*: Triggers payment retry, fraud review, or manual refund processing.
3. **message_logistics_team**:
   - *Parameters*: carrier: str, issue_type: str, inquiry_details: str
   - *Purpose*: Escalates carrier delays, lost parcels, or requests priority rerouting.
4. **message_customer**:
   - *Parameters*: channel: 'email' | 'sms', message_body: str, sentiment_tone: str
   - *Purpose*: Proactively informs customer of order updates, delays, or resolutions.
5. **create_internal_note**:
   - *Parameters*: 
ote_type: 'observation' | 'flag' | 'audit', content: str
   - *Purpose*: Internal supervisor scratchpad and audit trail.

#### Runtime Control Tools:
1. **schedule_next_wake_up**:
   - *Parameters*: duration_minutes: int, wake_up_reason: str
   - *Purpose*: Directs Temporal workflow how long to sleep before periodic review.
2. **update_memory_summary**:
   - *Parameters*: 
ew_summary: str
   - *Purpose*: Updates the rolling compact memory string.
3. **escalate_issue**:
   - *Parameters*: department: str, severity: 'MEDIUM' | 'HIGH' | 'CRITICAL', 
eason: str
   - *Purpose*: Flags the order as ESCALATED for human operator intervention.

---

## 5. Database Schema & Persistence

`mermaid
erDiagram
    SUPERVISOR ||--o{ ORDER_RUN : "configures"
    ORDER_RUN ||--o{ ACTIVITY_LOG : "records"

    SUPERVISOR {
        string id PK
        string name
        string base_instruction
        string available_tools
        string wake_up_policy
        string model_name
        datetime created_at
    }

    ORDER_RUN {
        string id PK "run_id (e.g. run_abc123)"
        string order_id "Order reference (e.g. ORD-9081)"
        string supervisor_id FK
        string status "ACTIVE | SLEEPING | ESCALATED | COMPLETED | TERMINATED"
        json order_context "Item, Customer, Address, Total"
        text compact_memory "Rolling memory summary"
        text runtime_instructions "Live operator notes"
        datetime next_wake_time
        datetime last_wake_time
        json final_summary "End of run post-mortem"
        datetime created_at
        datetime updated_at
    }

    ACTIVITY_LOG {
        string id PK
        string run_id FK
        string log_type "EVENT | CLASSIFICATION | REASONING | TOOL_EXECUTION | INSTRUCTION | FINAL_SUMMARY"
        string trigger_source "START | SIGNAL | TIMER | OPERATOR"
        string title
        text details
        json metadata_payload
        datetime timestamp
    }
`

---

## 6. REST API Specification

### 6.1. Supervisor Templates
- POST /api/supervisors: Create a supervisor configuration template.
- GET /api/supervisors: List all available templates (e.g. "Standard E-commerce", "VIP Expeditor", "High-Risk Fraud Monitor").
- GET /api/supervisors/{id}: Retrieve template details.

### 6.2. Order Runs
- POST /api/runs: Launch a new order run (Initializes database record and starts Temporal workflow).
  `json
  {
    "order_id": "ORD-1001",
    "supervisor_id": "sup_default",
    "order_context": {
      "customer_name": "Jay Talaviya",
      "customer_email": "talaviyajay10@gmail.com",
      "items": [{"name": "Gaming Laptop", "price": 1200, "qty": 1}],
      "priority": "HIGH"
    }
  }
  `
- GET /api/runs: List order runs (filters: status, search by order_id).
- GET /api/runs/{run_id}: Retrieve detailed run state, memory, and next wake time.
- GET /api/runs/{run_id}/timeline: Retrieve full activity and event log stream.

### 6.3. Event Simulator & Real-time Signals
- POST /api/runs/{run_id}/events: Inject an order event into the active workflow.
  `json
  {
    "event_type": "shipment_delayed",
    "payload": {
      "carrier": "FedEx",
      "delay_hours": 48,
      "reason": "Severe weather conditions at regional hub"
    }
  }
  `
- POST /api/runs/{run_id}/instructions: Inject real-time operator instructions.
  `json
  {
    "instruction": "For this order, prioritize speed over cost. If delayed further, authorize priority air shipping."
  }
  `
- POST /api/runs/{run_id}/interrupt: Pause the active run.
- POST /api/runs/{run_id}/resume: Resume a paused run.
- POST /api/runs/{run_id}/terminate: Force terminate the workflow with reason.

---

## 7. Frontend User Experience & UI Wireframe

### Dashboard View (/)
- **Metric Cards**: Total Runs, Active Supervisors, Sleeping/Awaiting Timer, Escalated Orders, Completed Orders.
- **Run Table**: Order ID, Supervisor Template, Current Status Badge, Sleep/Wake Countdown, Last Activity Timestamp, Action Buttons.
- **"New Order" Modal**: Launch an order with pre-filled sample templates.

### Run Inspector View (/runs/[id])
`
+----------------------------------------------------------------------------------------------------+
| Order Run: ORD-1001 [ HIGH PRIORITY ]               Status: [ SLEEPING - Wakes in 00:14:32 ]       |
+----------------------------------------------------+-----------------------------------------------+
| ?? LIVE ACTIVITY TIMELINE                          | ?? CURRENT COMPACT MEMORY                     |
|                                                    | "Order placed with 1x Gaming Laptop. Payment  |
| 10:00:01 [ORDER_CREATED] Order initialized         | confirmed. Shipment delayed by 48h (Weather). |
| 10:00:03 [AGENT] Initial review complete           | Customer emailed with revised ETA. Logistics  |
|          Action: schedule_next_wake_up(30m)        | team notified. Next check at 10:30."          |
| 10:05:22 [EVENT] shipment_delayed (48h)            +-----------------------------------------------+
| 10:05:23 [CLASSIFIER] Judged: URGENT (Wake Agent)  | ? EVENT SIMULATOR PANEL                      |
| 10:05:25 [AGENT REASONING] Delay exceeds SLA       | [?? Shipment Delayed]  [?? Payment Failed]    |
|          Action: message_customer(email, "...")    | [?? Customer Inquired] [? No Update (24h)]   |
|          Action: message_logistics_team("...")     | [?? Refund Requested]  [? Order Delivered]   |
| 10:05:26 [AGENT] Updated memory & scheduled wake   +-----------------------------------------------+
|          Action: schedule_next_wake_up(25m)        | ?? LIVE OPERATOR INSTRUCTIONS                 |
|                                                    | [ "Prioritize speed over cost..." ] [Send]    |
|                                                    +-----------------------------------------------+
|                                                    | ?? WORKFLOW CONTROLS                          |
|                                                    | [ ?? Pause ]  [ ?? Resume ]  [ ?? Terminate ] |
+----------------------------------------------------+-----------------------------------------------+
`

---

## 8. Step-by-Step Execution Plan

### Step 1: Project Scaffolding
- Initialize ackend/ with FastAPI, virtual environment (ackend/venv), dependencies, and .env.
- Initialize rontend/ with Next.js 15 (App Router), TypeScript, and Tailwind CSS.

### Step 2: Database Layer & Domain Models
- Define Supervisor, OrderRun, and ActivityLog SQLModel models in ackend/app/models/.
- Configure SQLite database engine in ackend/app/core/db.py.

### Step 3: Temporal Workflow & Gemini Agent Activities
- Set up Temporal client in ackend/app/temporal/client.py.
- Define OrderSupervisorWorkflow with signal definitions and sleep timers in ackend/app/temporal/workflows.py.
- Implement activities: classify_event_activity, 
un_agent_step_activity, inalize_run_activity in ackend/app/temporal/activities.py.
- Implement Temporal worker entry script ackend/run_worker.py.

### Step 4: FastAPI Routes & Event Dispatcher
- Implement supervisor routes, run management routes, event simulator routes, and live instruction routes in ackend/app/api/.

### Step 5: Next.js Frontend Dashboard & Simulator
- Build layout, run list dashboard, and interactive run inspector.
- Build event simulator panel with 1-click preset triggers.
- Build live instruction input and workflow control actions.

### Step 6: End-to-End Testing, Documentation & Walkthrough Script
- Run 3 complete simulation test scenarios.
- Verify that every acceptance criterion is satisfied.
- Generate ARCHITECTURE.md and complete README.md.
