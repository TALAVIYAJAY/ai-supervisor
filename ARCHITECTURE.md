# Order Supervisor: System Architecture & Design Note

## 1. Overview
The **Order Supervisor** is an autonomous AI system designed to oversee the lifecycle of a single order from placement to completion. Built with **Temporal**, **FastAPI**, **Google Gemini 3.7 Flash**, and **Next.js 15**, it implements a tri-triggered, 2-tier intelligent wake/sleep workflow model.

---

## 2. Key Architecture Components

### A. Temporal Long-Running Workflow per Order
- **Model**: One durable OrderSupervisorWorkflow instance per order (order-supervisor-<run_id>).
- **Sleep / Wake Execution**: The workflow maintains durable state without consuming CPU cycles while awaiting timers or signals.
- **Triggers**:
  1. **Workflow Start**: Runs initial assessment, sends initial notifications, and computes sleep duration.
  2. **External Signals**: Receives order lifecycle events (payment_failed, shipment_delayed, customer_message_received, 
efund_requested, delivered).
  3. **Scheduled Timers**: Wakes on interval expiration to inspect order SLA and carrier checkpoints.

### B. 2-Tier Intelligent Event Handling
- **Tier 1 (Lightweight Classifier / Policy Activity)**:
  - Sub-second evaluation via Gemini 3.7 Flash (	emperature=0.1).
  - Classifies events into WAKE_NOW (urgent) or REMAIN_ASLEEP (informational), preserving token efficiency and system throughput.
- **Tier 2 (Main Supervisor Agent Activity)**:
  - Multi-turn tool execution loop powered by Gemini 3.7 Flash with function declarations.
  - Executes business tools (message_customer, message_logistics_team, message_fulfillment_team, message_payments_team, create_internal_note).
  - Updates rolling compact memory and schedules the next sleep duration.

### C. Context Compaction & State Persistence
- **Rolling Memory**: Instead of passing growing conversational history, the agent generates and updates a compact chronological summary (compact_memory).
- **Database Schema**:
  - supervisors: Configurable prompt templates, sensitivity policies, and toolsets.
  - order_runs: Order state, rolling memory, next wake-up timestamps, and post-mortem summary.
  - ctivity_logs: Complete chronological timeline of events, classifier decisions, thoughts, and executed tools.

---

## 3. Data Flow Diagram

`mermaid
sequenceDiagram
    autonumber
    actor Operator as Next.js Dashboard / Simulator
    participant API as FastAPI Backend
    participant WF as Temporal Workflow
    participant Classify as Tier-1 Classifier
    participant Agent as Tier-2 Agent & Tools
    participant DB as PostgreSQL Database

    Operator->>API: Inject Event (e.g. shipment_delayed)
    API->>WF: Send Signal ('event_signal')
    WF->>Classify: Execute classify_event_activity
    Classify-->>WF: Decision: WAKE_NOW (Urgent)

    WF->>Agent: Execute run_agent_step_activity
    Agent->>Agent: Execute Tools (message_customer, message_logistics)
    Agent-->>WF: Tool Results + New Compact Memory + Sleep Duration (60m)
    WF->>DB: Log Actions & Update Status to SLEEPING
    WF->>WF: Sleep until Timer / Next Signal
`

---

## 4. End-of-Run Post-Mortem
When the order reaches terminal status (delivered, 
efund_completed, cancelled), the workflow invokes inalize_run_activity to produce:
- Executive Order Summary
- Important Actions Taken
- Key Learnings
- Process & SLA Improvement Recommendations
