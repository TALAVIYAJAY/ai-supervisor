import asyncio
import logging
from temporalio.worker import Worker
from app.config import settings
from app.api import get_temporal_client
from app.workflows import (
    OrderSupervisorWorkflow,
    classify_event_activity,
    run_agent_step_activity,
    record_activity_log_activity,
    update_order_run_state_activity,
    finalize_run_activity
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("temporal_worker")

async def main():
    logger.info(f"Connecting to Temporal Server at {settings.TEMPORAL_HOST}...")
    client = await get_temporal_client()
    
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
    
    logger.info(f"🚀 Temporal Worker started on task queue '{settings.TEMPORAL_TASK_QUEUE}'")
    logger.info("Listening for order supervisor workflows and incoming signals...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
