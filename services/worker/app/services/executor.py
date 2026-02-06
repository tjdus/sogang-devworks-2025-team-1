import time

from sqlalchemy.ext.asyncio import AsyncSession

from services.common.logging_utils import setup_logger
from services.common.metrics import REQUEST_COUNT, REQUEST_LATENCY
from services.worker.app.agents.worker_agent import build_worker_chain
from services.worker.app.services.prompt_loader import load_active_prompt

logger = setup_logger("worker.executor")


async def execute_task(db: AsyncSession, task_type: str, refined_input: str) -> tuple[str, int, int]:
    """Execute a task with the current active prompt. Returns (output, prompt_version, latency_ms)."""
    # Load the latest active prompt from DB (core self-healing mechanism)
    system_prompt, prompt_version = await load_active_prompt(db, task_type)

    # Build chain with dynamic prompt and execute
    chain = build_worker_chain(system_prompt)

    start = time.time()
    output = await chain.ainvoke({"refined_input": refined_input})
    latency_ms = int((time.time() - start) * 1000)

    REQUEST_COUNT.labels(service="worker", task_type=task_type, status="success").inc()
    REQUEST_LATENCY.labels(service="worker", endpoint="/api/v1/task").observe(latency_ms / 1000)

    logger.info("task_executed", extra={
        "task_type": task_type,
        "prompt_version": prompt_version,
        "latency_ms": latency_ms,
        "output_length": len(output),
    })

    return output, prompt_version, latency_ms
