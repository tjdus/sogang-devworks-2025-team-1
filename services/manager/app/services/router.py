from uuid import UUID

import httpx

from services.common.config import get_settings
from services.common.logging_utils import setup_logger
from services.common.schemas import TaskInput, TaskOutput, EvaluateInput, EvaluateOutput, EvaluationDetail

logger = setup_logger("manager.router")


async def call_worker(request_id: UUID, task_type: str, refined_input: str) -> TaskOutput:
    settings = get_settings()
    payload = TaskInput(request_id=request_id, task_type=task_type, refined_input=refined_input)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.WORKER_URL}/api/v1/task",
                json=payload.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return TaskOutput(**resp.json())
    except httpx.ConnectError:
        logger.error("worker_unreachable", extra={"request_id": str(request_id)})
        raise RuntimeError(f"Worker service unreachable at {settings.WORKER_URL}")
    except httpx.TimeoutException:
        logger.error("worker_timeout", extra={"request_id": str(request_id)})
        raise RuntimeError(f"Worker service timed out at {settings.WORKER_URL}")


async def call_evaluator(
    request_id: UUID, task_type: str,
    user_input: str, refined_input: str, worker_output: str,
) -> EvaluateOutput:
    settings = get_settings()
    payload = EvaluateInput(
        request_id=request_id,
        task_type=task_type,
        user_input=user_input,
        refined_input=refined_input,
        worker_output=worker_output,
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.EVALUATOR_URL}/api/v1/evaluate",
                json=payload.model_dump(mode="json"),
            )
            resp.raise_for_status()
            return EvaluateOutput(**resp.json())
    except httpx.ConnectError:
        logger.error("evaluator_unreachable", extra={"request_id": str(request_id)})
        raise RuntimeError(f"Evaluator service unreachable at {settings.EVALUATOR_URL}")
    except httpx.TimeoutException:
        logger.error("evaluator_timeout", extra={"request_id": str(request_id)})
        raise RuntimeError(f"Evaluator service timed out at {settings.EVALUATOR_URL}")
