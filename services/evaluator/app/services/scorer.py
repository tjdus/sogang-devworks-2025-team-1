from services.common.logging_utils import setup_logger
from services.common.metrics import EVALUATION_SCORE, EVALUATION_PASS_TOTAL
from services.evaluator.app.agents.evaluator_agent import evaluate_with_llm
from services.evaluator.app.services.validators import validate_output

logger = setup_logger("evaluator.scorer")

PASS_THRESHOLD = 0.7
RULE_WEIGHT = 0.4
LLM_WEIGHT = 0.6


async def compute_score(
    task_type: str,
    user_input: str,
    refined_input: str,
    worker_output: str,
) -> tuple[float, bool, dict]:
    """Compute combined score. Returns (score, passed, detail_dict)."""

    # Rule-based validation (40%)
    rule_result = validate_output(worker_output, task_type)

    # LLM-based evaluation (60%)
    llm_result = await evaluate_with_llm(user_input, refined_input, worker_output)

    # Weighted combination
    combined_score = round(
        rule_result["score"] * RULE_WEIGHT + llm_result["score"] * LLM_WEIGHT,
        3,
    )
    passed = combined_score >= PASS_THRESHOLD

    # Record metrics
    EVALUATION_SCORE.labels(task_type=task_type).observe(combined_score)
    EVALUATION_PASS_TOTAL.labels(
        task_type=task_type,
        result="pass" if passed else "fail",
    ).inc()

    detail = {
        "rule_score": rule_result["score"],
        "llm_score": llm_result["score"],
        "rule_details": rule_result["details"],
        "llm_details": llm_result["details"],
    }

    logger.info("score_computed", extra={
        "task_type": task_type,
        "rule_score": rule_result["score"],
        "llm_score": llm_result["score"],
        "combined_score": combined_score,
        "passed": passed,
    })

    return combined_score, passed, detail
