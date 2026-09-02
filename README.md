# AI Supervisor (Order Supervisor POC)

A long-running, autonomous AI Supervisor for e-commerce and order operations powered by **Temporal**, **FastAPI**, **Google Gemini**, and **Next.js**.

## Overview
This system orchestrates and oversees the entire lifecycle of an order from creation to terminal completion (delivery, cancellation, or refund).

### Key Features
- **Long-Running Temporal Workflow**: One workflow per order, sleeping efficiently and waking on scheduled timers or incoming signals.
- **2-Tier Agent Architecture**:
  - **Lightweight Event Classifier**: Filters and assesses event urgency before waking the main agent.
  - **Main Supervisor Agent**: Full reasoning loop with tool execution (message_customer, message_logistics_team, message_fulfillment_team, message_payments_team, create_internal_note).
- **Context & Memory Compaction**: Rolling memory summary to optimize LLM context length and token efficiency.
- **Interactive Event Simulator**: Inject real-time order lifecycle events and live operator instructions.
- **Next.js Modern Dashboard**: Real-time run inspector, timeline view, and supervisor template configuration.
- **Hybrid Refresh & Self-Healing**: Automatically synchronizes and self-heals workflow state with Temporal.

---

## Running the Application (Only 2 Terminals Needed!)

The backend embeds the **Temporal Worker directly into the FastAPI process**, so you only need **2 terminals**:

### 1. Terminal 1: Backend (FastAPI + Embedded Temporal Worker)
```powershell
cd D:\Django\AI_SUPERVISOR\backend
python manage.py runserver
```
* **API Documentation**: http://localhost:8000/docs
* **Backend Health**: http://localhost:8000/health

### 2. Terminal 2: Frontend (Next.js Dashboard)
```powershell
cd D:\Django\AI_SUPERVISOR\frontend
npm run dev
```
* **Dashboard URL**: http://localhost:3000

---

## Testing / Walkthrough Flow

1. Open **http://localhost:3000** in your browser.
2. Click **"Launch New Order"** (select the Gaming Laptop preset).
3. Open the newly launched order run in the **Run Inspector**.
4. Use the **Event Generator** panel on the right:
   - Click **"Shipment Delayed (48h)"** -> Watch the Tier-1 classifier trigger the Tier-2 agent to notify the customer and logistics team.
   - Click **"Customer Message"** -> Observe real-time response and rolling memory update.
   - Add a **Live Operator Instruction** (e.g., *"Prioritize speed over cost"*).
   - Click **"Order Delivered"** -> Watch the workflow close and view the **Final Learnings & Post-Mortem Report**.

