from sqlalchemy.ext.asyncio import AsyncSession

from services.common.logging_utils import setup_logger
from services.common.models import OptimizationReport

logger = setup_logger("optimizer.reporter")


async def save_report(db: AsyncSession, optimization_info: dict) -> OptimizationReport:
    """Save an optimization report to the database."""
    report = OptimizationReport(
        task_type=optimization_info["task_type"],
        before_prompt_version=optimization_info["before_version"],
        before_prompt_content=optimization_info["before_content"],
        after_prompt_version=optimization_info["after_version"],
        after_prompt_content=optimization_info["after_content"],
        failure_analysis=optimization_info["failure_analysis"],
        triggered_by="optimizer",
    )
    db.add(report)
    await db.commit()

    logger.info("report_saved", extra={
        "task_type": optimization_info["task_type"],
        "report_id": report.id,
    })
    return report


def format_report(optimization_info: dict) -> str:
    """Format a human-readable optimization report."""
    analysis = optimization_info.get("failure_analysis", {})
    return f"""
=== Self-Healing Optimization Report ===
Task Type: {optimization_info['task_type']}
Failures Analyzed: {optimization_info['failure_count']}

--- Before (v{optimization_info['before_version']}) ---
{optimization_info['before_content'][:500]}

--- Failure Analysis ---
Patterns: {', '.join(analysis.get('failure_patterns', []))}
Root Causes: {', '.join(analysis.get('root_causes', []))}

--- After (v{optimization_info['after_version']}) ---
{optimization_info['after_content'][:500]}

--- Improvements Applied ---
{chr(10).join('- ' + s for s in analysis.get('improvement_suggestions', []))}
========================================
"""
