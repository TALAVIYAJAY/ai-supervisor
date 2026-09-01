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
