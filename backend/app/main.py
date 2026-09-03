import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .config import settings
from .db import engine, create_db_and_tables
from .models import Supervisor, OrderRun
from .api import router as v1_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("order_supervisor")

def seed_default_supervisors():
    """Seed baseline supervisor templates into PostgreSQL if table is empty."""
    with Session(engine) as session:
        existing = session.exec(select(Supervisor)).first()
        if not existing:
            default_sup = Supervisor(
                name="Standard E-commerce Supervisor",
                description="Balanced supervisor for standard retail orders. Prioritizes customer notification and prompt logistics escalations.",
                wake_up_policy="balanced",
                available_tools=[
                    "message_fulfillment_team",
                    "message_payments_team",
                    "message_logistics_team",
                    "message_customer",
                    "create_internal_note",
                    "schedule_next_wake_up",
                    "update_memory_summary",
                    "escalate_issue",
                    "close_workflow"
                ],
                base_instruction="""You are an autonomous Order Operations Supervisor for standard e-commerce orders.
Monitor the entire fulfillment lifecycle.
When delays or exceptions happen:
1. Message the customer proactively to reassure them.
2. Message logistics or fulfillment teams to expedite movement.
3. Update the rolling compact memory summary with key milestones.
4. Schedule periodic wake-up reviews (30-60 mins) to track progress."""
            )
            vip_sup = Supervisor(
                name="VIP Priority Expeditor",
                description="High-touch aggressive supervisor for premium customers. Zero-tolerance for delays, instant escalation.",
                wake_up_policy="aggressive",
                available_tools=[
                    "message_fulfillment_team",
                    "message_payments_team",
                    "message_logistics_team",
                    "message_customer",
                    "create_internal_note",
                    "schedule_next_wake_up",
                    "update_memory_summary",
                    "escalate_issue",
                    "close_workflow"
                ],
                base_instruction="""You are an autonomous VIP Order Expeditor.
This order is for a Tier-1 VIP customer.
On ANY delay or delivery risk:
1. Immediately alert fulfillment leadership and logistics.
2. Provide personalized customer communication.
3. Schedule frequent wake-ups (15-30 mins) to verify every handoff."""
            )
            session.add(default_sup)
            session.add(vip_sup)
            session.commit()
            logger.info("Seeded default supervisor templates.")

async def start_embedded_temporal_worker():
    """
    Embedded Temporal Worker running directly inside FastAPI's async event loop.
    Enables running the entire backend (API + Worker) in ONE single terminal!
    """
    try:
        from temporalio.worker import Worker
        from .api import get_temporal_client
        from .workflows import (
            OrderSupervisorWorkflow,
            classify_event_activity,
            run_agent_step_activity,
            record_activity_log_activity,
            update_order_run_state_activity,
            finalize_run_activity
        )

        logger.info(f"Connecting embedded Temporal Worker to {settings.TEMPORAL_HOST}...")
        client = await get_temporal_client()
        if not client:
            logger.info(f"Temporal server at {settings.TEMPORAL_HOST} not detected. Direct Autonomous State Machine engine is ACTIVE.")
            return

        worker = Worker(
            client,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
            workflows=[OrderSupervisorWorkflow],
            activities=[
                classify_event_activity,
                run_agent_step_activity,
                record_activity_log_activity,
                update_order_run_state_activity,
                finalize_run_activity
            ]
        )
        logger.info(f"🚀 Embedded Temporal Worker active on queue: '{settings.TEMPORAL_TASK_QUEUE}'")
        await worker.run()
    except asyncio.CancelledError:
        logger.info("Embedded Temporal Worker received stop signal.")
    except Exception as e:
        logger.warning(f"Embedded Temporal Worker offline (Temporal Server at {settings.TEMPORAL_HOST} not reachable): {e}")

async def scheduled_wake_up_ticker():
    """
    Background Autonomous Ticker:
    Checks every 10 seconds for sleeping runs whose next_wake_time has passed
    (e.g., overnight while server was off, or when a timer countdown finishes),
    and automatically triggers their periodic review!
    """
    from datetime import datetime, timezone
    from sqlmodel import Session, select
    from .db import engine
    from .models import OrderRun
    from .workflows import execute_direct_scheduled_wakeup

    logger.info("⏰ Autonomous Scheduled Wake-Up Ticker active.")
    # Run an initial check after 2 seconds
    await asyncio.sleep(2)
    while True:
        try:
            now = datetime.now()
            with Session(engine) as session:
                overdue_runs = session.exec(
                    select(OrderRun).where(
                        OrderRun.status == "SLEEPING",
                        OrderRun.next_wake_time != None,
                        OrderRun.next_wake_time <= now
                    )
                ).all()

                for r in overdue_runs:
                    logger.info(f"⏰ Auto-waking overdue run {r.id} (Order {r.order_id})...")
                    asyncio.create_task(execute_direct_scheduled_wakeup(r.id))

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Error in wake-up ticker: {e}")

        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Order Supervisor Backend...")
    try:
        create_db_and_tables()
        seed_default_supervisors()
    except Exception as e:
        logger.warning(f"Database initialization: {e}")

    # Launch embedded Temporal Worker & Scheduled Wake-Up Ticker in background
    worker_task = asyncio.create_task(start_embedded_temporal_worker())
    ticker_task = asyncio.create_task(scheduled_wake_up_ticker())
    
    yield
    
    logger.info("Shutting down Order Supervisor Backend...")
    worker_task.cancel()
    ticker_task.cancel()
    await asyncio.sleep(0.5)

app = FastAPI(
    title="Order Supervisor API",
    description="Autonomous Long-Running AI Workflow Backend powered by Temporal, FastAPI, and Google Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": settings.get_database_url().split("@")[-1],
        "environment": settings.ENVIRONMENT,
        "model": settings.GEMINI_MODEL
    }
