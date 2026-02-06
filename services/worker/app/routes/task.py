from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.db import get_db
from services.common.logging_utils import setup_logger
from services.common.schemas import TaskInput, TaskOutput
from services.worker.app.services.executor import execute_task

logger = setup_logger("worker.task")
router = APIRouter()


@router.post("/task", response_model=TaskOutput)
async def handle_task(
    body: TaskInput,
    db: AsyncSession = Depends(get_db),
):
    logger.info("task_received", extra={
        "request_id": str(body.request_id),
        "task_type": body.task_type,
    })

    try:
        output, prompt_version, latency_ms = await execute_task(
            db, body.task_type, body.refined_input,
        )
    except Exception as e:
        logger.error("task_execution_failed", extra={
            "request_id": str(body.request_id),
            "task_type": body.task_type,
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")

    return TaskOutput(
        request_id=body.request_id,
        output=output,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
    )
