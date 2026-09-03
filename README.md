# Autonomous AI Order Supervisor

A long-running, autonomous AI Supervisor for e-commerce and order operations powered by **Temporal**, **FastAPI**, **Google Gemini 3.5 Flash**, **PostgreSQL**, and **Next.js 15**.

---

## Overview

The **Autonomous AI Order Supervisor** oversees the end-to-end lifecycle of an e-commerce order from placement to final fulfillment. Rather than using stateless chatbots or brittle polling scripts, it assigns a dedicated, durable AI supervisor to each order that sleeps efficiently when idle and wakes up autonomously on real-world events or scheduled timers.

### Key Capabilities:
- **Long-Running Workflows**: One durable workflow per order, sleeping efficiently and maintaining state across days.
- **2-Tier Intelligent Architecture**:
  - **Tier-1 Event Classifier**: Lightweight, sub-second evaluation to decide whether an event requires agent wake-up.
  - **Tier-2 Supervisor Agent**: Full reasoning loop with multi-turn tool calling (`message_customer`, `message_fulfillment_team`, `message_payments_team`, `message_logistics_team`, `create_internal_note`).
- **Context Compaction**: Maintains a rolling compact memory summary across sleeps to eliminate prompt bloat.
- **Operator Guidance & Security Defense**: Live runtime instruction injection protected by a 3-layer security firewall against prompt injections, SQL syntax, XSS scripts, and out-of-domain spam.
- **Workflow Lifecycle Controls**: Full operational authority with Pause, Resume, Force Wake, and Terminate.
- **Post-Mortem Analytics**: Automatically compiles an executive summary, actions taken, key learnings, and recommendations when the order concludes.

---

## What the System Looks Like

### 1. Frontend Dashboard (`http://localhost:3000`)
The user interface is designed as an intuitive single-page operations console:
- **Header & Health Bar**: Shows backend connection status, model configuration, and navigation to supervisor templates.
- **Operational KPI Cards**: Real-time counters showing Total Runs, Active Supervisors, Sleeping Orders, Paused Runs, and Completed Orders.
- **Interactive Orders Table**: Complete list of orders with status badges (`ACTIVE`, `SLEEPING`, `PAUSED`, `COMPLETED`), delivery SLA targets, and local time (IST) next wake-up timestamps.
- **Single-Page Inspector (Zero Tabs)**: Clicking any order opens a unified inspection panel directly below the table:
  - **Banner**: Displays Order ID, live status, next wake-up time, and the AI's **Rolling Compact Memory**.
  - **Action Panel**: 
    - **Event Generator & Simulator**: 6 preset signal buttons (`Shipment Delayed`, `Payment Failed`, `Customer Message`, `No Update 24h`, `Refund Requested`, `Order Delivered`).
    - **Live Operator Instructions**: Input box with quick directive chips (`🛑 Cancel order`, `⚡ Prioritize speed`, `📦 Hold shipment`).
    - **Workflow Lifecycle Controls**: One-click `Pause`, `Resume`, `Force Wake`, and `Terminate Workflow`.
  - **Live Activity Timeline**: Real-time chronological audit trail displaying every incoming signal, Tier-1 classification decision, thought process, and tool action taken.
  - **Post-Mortem Card**: When completed, displays a report with Executive Summary, Actions Taken, Key Learnings, and Recommendations.

### 2. Backend Operations (`http://localhost:8000`)
- **FastAPI Interactive API Docs**: Swagger UI available at `http://localhost:8000/docs` for testing every endpoint.
- **Health & Diagnostics**: Endpoint at `http://localhost:8000/health` reporting database connectivity and active LLM configuration.
- **Embedded Dual Engine**: Seamlessly executes workflows through Temporal or an embedded state machine with a 10s background watchdog ticker.
- **Automated Seeding**: Automatically populates `supervisors` table with Standard and VIP Priority templates if empty.

---

---

## Environment Variables Configuration

To run the project, create one `.env` file in the **backend** folder and one `.env` file in the **frontend** folder with the following variables:

### 1. Backend Environment (`backend/.env`)
Create a file named `.env` inside the `backend/` directory:

```env
# Google Gemini API Configuration
# Get your API key from Google AI Studio: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# PostgreSQL Database Connection Settings
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_supervisor
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/ai_supervisor

# Temporal Orchestrator Host (Optional: embedded fail-safe active if offline)
TEMPORAL_HOST=localhost:7233

# Operational Settings
ENVIRONMENT=development
PORT=8000
```

---

### 2. Frontend Environment (`frontend/.env`)
Create a file named `.env` inside the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Setup Instructions (Running on Any System)

Follow these simple, step-by-step instructions to set up and run this project on any system (Windows, macOS, or Linux).

### Prerequisites:
- **Python 3.10+** installed
- **Node.js 18+** & npm installed
- **PostgreSQL** database running (create a database named `ai_supervisor`)

---

### Step 1: Clone the Repository
```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI_SUPERVISOR
```

---

### Step 2: Backend Setup (FastAPI + Embedded Engine)

1. Open your terminal in the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your `.env` file inside the `backend/` folder:
   ```env
   # backend/.env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite

   # PostgreSQL Database Connection Settings
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ai_supervisor
   DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/ai_supervisor

   # Operational Settings
   ENVIRONMENT=development
   PORT=8000
   ```

5. Initialize the database schema:
   ```bash
   python manage.py migrate
   ```

6. Start the backend server:
   ```bash
   python manage.py runserver
   ```
   * The backend will start on **`http://localhost:8000`**.
   * Interactive Swagger Docs: **`http://localhost:8000/docs`**
   * Health Check: **`http://localhost:8000/health`**

---

### Step 3: Frontend Setup (Next.js Dashboard)

1. Open a second terminal window in the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install frontend dependencies:
   ```bash
   npm install
   ```

3. Create your `.env` file inside the `frontend/` folder:
   ```env
   # frontend/.env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```
   * Open your browser at **`http://localhost:3000`** to access the dashboard.

---

### Step 4: Verify with Automated Tests

To verify that all 8 operational scenarios (template auto-seeding, workflow lifecycle, Tier-1 classification, tool calling, security guardrails, post-mortem generation) pass on your machine:

```bash
cd backend
python manage.py test
```

---

## Detailed System Documentation

For deep technical architecture, sequence diagrams, database schemas, and tool definitions, refer to:
* **[documentation.md](documentation.md)**
