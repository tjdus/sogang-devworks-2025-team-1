from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from services.common.config import get_settings
from services.common.logging_utils import setup_logger
from services.common.models import ExecutionLog

logger = setup_logger("optimizer.log_analyzer")


async def get_failure_logs(db: AsyncSession, task_type: str) -> list[ExecutionLog]:
    """Fetch recent failed execution logs."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.OPTIMIZER_LOOKBACK_MINUTES)

    stmt = (
        select(ExecutionLog)
        .where(
            and_(
                ExecutionLog.task_type == task_type,
                ExecutionLog.evaluation_passed == False,
                ExecutionLog.created_at >= cutoff,
            )
        )
        .order_by(ExecutionLog.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_failure_count(db: AsyncSession, task_type: str) -> int:
    """Count recent failures for a task type."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.OPTIMIZER_LOOKBACK_MINUTES)

    stmt = (
        select(func.count())
        .select_from(ExecutionLog)
        .where(
            and_(
                ExecutionLog.task_type == task_type,
                ExecutionLog.evaluation_passed == False,
                ExecutionLog.created_at >= cutoff,
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


async def get_task_types_needing_optimization(db: AsyncSession) -> list[str]:
    """Find task types with failures exceeding the threshold."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.OPTIMIZER_LOOKBACK_MINUTES)

    stmt = (
        select(ExecutionLog.task_type, func.count().label("fail_count"))
        .where(
            and_(
                ExecutionLog.evaluation_passed == False,
                ExecutionLog.created_at >= cutoff,
            )
        )
        .group_by(ExecutionLog.task_type)
        .having(func.count() >= settings.OPTIMIZER_FAILURE_THRESHOLD)
    )
    result = await db.execute(stmt)
    task_types = [row[0] for row in result.all()]

    logger.info("task_types_needing_optimization", extra={
        "task_types": task_types,
        "threshold": settings.OPTIMIZER_FAILURE_THRESHOLD,
    })
    return task_types
