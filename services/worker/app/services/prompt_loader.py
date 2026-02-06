from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.logging_utils import setup_logger
from services.common.models import Prompt
from services.common.metrics import PROMPT_VERSION

logger = setup_logger("worker.prompt_loader")


async def load_active_prompt(db: AsyncSession, task_type: str) -> tuple[str, int]:
    """Load the current active prompt from DB. Returns (content, version)."""
    stmt = (
        select(Prompt)
        .where(Prompt.task_type == task_type, Prompt.is_active == True)
        .order_by(Prompt.version.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    prompt = result.scalar_one_or_none()

    if prompt is None:
        logger.warning("no_active_prompt", extra={"task_type": task_type})
        raise ValueError(f"No active prompt found for task_type={task_type}")

    PROMPT_VERSION.labels(task_type=task_type).set(prompt.version)
    logger.info("prompt_loaded", extra={
        "task_type": task_type,
        "version": prompt.version,
        "content_length": len(prompt.content),
    })
    return prompt.content, prompt.version
