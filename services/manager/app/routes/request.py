import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.db import get_db
from services.common.logging_utils import setup_logger
from services.common.metrics import REQUEST_COUNT, REQUEST_LATENCY
from services.common.schemas import RequestInput, RequestResponse
from services.manager.app.services.refiner import refine_request
from services.manager.app.services.router import call_worker, call_evaluator

logger = setup_logger("manager.request")
router = APIRouter()


@router.post("/request", response_model=RequestResponse)
async def handle_request(
    body: RequestInput,
    db: AsyncSession = Depends(get_db),
):
    start = time.time()
    request_id = uuid.uuid4()

    logger.info("request_received", extra={"request_id": str(request_id), "task_type": body.task_type})

    try:
        # Step 1: Refine user input via LangChain
        refined_input = await refine_request(body.user_input, body.task_type)
        logger.info("request_refined", extra={"request_id": str(request_id)})

        # Step 2: Call Worker
        worker_result = await call_worker(request_id, body.task_type, refined_input)
        logger.info("worker_completed", extra={
            "request_id": str(request_id),
            "prompt_version": worker_result.prompt_version,
            "latency_ms": worker_result.latency_ms,
        })

        # Step 3: Call Evaluator
        eval_result = await call_evaluator(
            request_id, body.task_type, body.user_input, refined_input, worker_result.output,
        )
        logger.info("evaluation_completed", extra={
            "request_id": str(request_id),
            "score": eval_result.score,
            "passed": eval_result.passed,
        })

        # Step 4: Save execution log
        from services.common.models import ExecutionLog
        log = ExecutionLog(
            request_id=request_id,
            task_type=body.task_type,
            user_input=body.user_input,
            refined_input=refined_input,
            prompt_version=worker_result.prompt_version,
            worker_output=worker_result.output,
            worker_latency_ms=worker_result.latency_ms,
            evaluation_score=eval_result.score,
            evaluation_passed=eval_result.passed,
            evaluation_detail=eval_result.detail.model_dump(),
        )
        db.add(log)
        await db.commit()

        REQUEST_COUNT.labels(service="manager", task_type=body.task_type, status="success").inc()

        return RequestResponse(
            request_id=request_id,
            refined_input=refined_input,
            worker_output=worker_result.output,
            evaluation_score=eval_result.score,
            evaluation_passed=eval_result.passed,
            prompt_version=worker_result.prompt_version,
        )

    except Exception as e:
        REQUEST_COUNT.labels(service="manager", task_type=body.task_type, status="error").inc()
        logger.error("request_failed", extra={"request_id": str(request_id), "error": str(e)})

        # Save error log — wrapped so a DB failure doesn't mask the original error
        try:
            from services.common.models import ExecutionLog
            error_log = ExecutionLog(
                request_id=request_id,
                task_type=body.task_type,
                user_input=body.user_input,
                error_message=str(e),
            )
            db.add(error_log)
            await db.commit()
        except Exception as log_err:
            logger.error("error_log_save_failed", extra={
                "request_id": str(request_id),
                "log_error": str(log_err),
            })
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        elapsed = time.time() - start
        REQUEST_LATENCY.labels(service="manager", endpoint="/api/v1/request").observe(elapsed)
