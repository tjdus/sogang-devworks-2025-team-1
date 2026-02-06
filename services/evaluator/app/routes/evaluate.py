from fastapi import APIRouter, HTTPException

from services.common.logging_utils import setup_logger
from services.common.schemas import EvaluateInput, EvaluateOutput, EvaluationDetail
from services.evaluator.app.services.scorer import compute_score

logger = setup_logger("evaluator.evaluate")
router = APIRouter()


@router.post("/evaluate", response_model=EvaluateOutput)
async def handle_evaluate(body: EvaluateInput):
    logger.info("evaluate_received", extra={"request_id": str(body.request_id)})

    try:
        score, passed, detail = await compute_score(
            task_type=body.task_type,
            user_input=body.user_input,
            refined_input=body.refined_input,
            worker_output=body.worker_output,
        )
    except Exception as e:
        logger.error("evaluate_failed", extra={
            "request_id": str(body.request_id),
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

    return EvaluateOutput(
        request_id=body.request_id,
        score=score,
        passed=passed,
        detail=EvaluationDetail(**detail),
    )
