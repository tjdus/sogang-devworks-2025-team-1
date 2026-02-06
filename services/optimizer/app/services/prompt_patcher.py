from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.logging_utils import setup_logger
from services.common.models import Prompt
from services.common.metrics import OPTIMIZATION_RUNS, PROMPT_VERSION
from services.optimizer.app.agents.optimizer_agent import analyze_failures, generate_improved_prompt
from services.optimizer.app.services.log_analyzer import get_failure_logs

logger = setup_logger("optimizer.prompt_patcher")


async def get_current_prompt(db: AsyncSession, task_type: str) -> Prompt | None:
    stmt = (
        select(Prompt)
        .where(Prompt.task_type == task_type, Prompt.is_active == True)
        .order_by(Prompt.version.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def patch_prompt(db: AsyncSession, task_type: str) -> dict | None:
    """Analyze failures and patch the prompt. Returns optimization info or None."""

    # Get current active prompt
    current = await get_current_prompt(db, task_type)
    if current is None:
        logger.warning("no_active_prompt", extra={"task_type": task_type})
        return None

    # Get failure logs
    failures = await get_failure_logs(db, task_type)
    if not failures:
        logger.info("no_failures_found", extra={"task_type": task_type})
        return None

    # Prepare failure log summaries for LLM
    failure_summaries = []
    for f in failures[:10]:
        failure_summaries.append({
            "user_input": f.user_input[:200] if f.user_input else "",
            "worker_output": f.worker_output[:300] if f.worker_output else "",
            "score": f.evaluation_score,
            "eval_detail": f.evaluation_detail,
            "error": f.error_message,
        })

    # Step 1: Analyze failures
    logger.info("analyzing_failures", extra={
        "task_type": task_type,
        "failure_count": len(failures),
        "current_version": current.version,
    })
    analysis = await analyze_failures(current.content, failure_summaries)

    # Step 2: Generate improved prompt
    improved_content = await generate_improved_prompt(current.content, analysis)

    # Step 3 & 4: Deactivate current + insert new in a single transaction
    new_version = current.version + 1
    try:
        await db.execute(
            update(Prompt)
            .where(Prompt.task_type == task_type, Prompt.is_active == True)
            .values(is_active=False)
        )
        await db.flush()

        new_prompt = Prompt(
            task_type=task_type,
            content=improved_content,
            version=new_version,
            is_active=True,
            change_reason=f"Auto-optimized: {', '.join(analysis.get('root_causes', [])[:3])}",
            created_by="optimizer",
        )
        db.add(new_prompt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("prompt_patch_failed", extra={
            "task_type": task_type,
            "error": str(e),
        })
        raise

    # Update metrics
    OPTIMIZATION_RUNS.labels(task_type=task_type, result="success").inc()
    PROMPT_VERSION.labels(task_type=task_type).set(new_version)

    logger.info("prompt_patched", extra={
        "task_type": task_type,
        "before_version": current.version,
        "after_version": new_version,
    })

    return {
        "task_type": task_type,
        "before_version": current.version,
        "before_content": current.content,
        "after_version": new_version,
        "after_content": improved_content,
        "failure_analysis": analysis,
        "failure_count": len(failures),
    }
