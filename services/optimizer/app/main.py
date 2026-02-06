"""Optimizer service - runs as a standalone script (CronJob)."""
import asyncio
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.common.db import get_session_factory
from services.common.logging_utils import setup_logger
from services.common.metrics import OPTIMIZATION_RUNS
from services.optimizer.app.services.log_analyzer import get_task_types_needing_optimization
from services.optimizer.app.services.prompt_patcher import patch_prompt
from services.optimizer.app.services.reporter import save_report, format_report

logger = setup_logger("optimizer.main")


async def run_optimization_cycle():
    """Main optimization cycle - analyze failures and patch prompts."""
    logger.info("optimization_cycle_started")

    factory = get_session_factory()
    async with factory() as db:
        # Find task types that need optimization
        task_types = await get_task_types_needing_optimization(db)

        if not task_types:
            logger.info("no_optimization_needed")
            return

        for task_type in task_types:
            try:
                logger.info("optimizing_task_type", extra={"task_type": task_type})

                # Run the optimization
                result = await patch_prompt(db, task_type)

                if result:
                    # Save report
                    await save_report(db, result)

                    # Print human-readable report
                    report_text = format_report(result)
                    print(report_text)
                    logger.info("optimization_completed", extra={
                        "task_type": task_type,
                        "before_version": result["before_version"],
                        "after_version": result["after_version"],
                    })
                else:
                    logger.info("optimization_skipped", extra={"task_type": task_type})

            except Exception as e:
                OPTIMIZATION_RUNS.labels(task_type=task_type, result="error").inc()
                logger.error("optimization_failed", extra={
                    "task_type": task_type,
                    "error": str(e),
                })

    logger.info("optimization_cycle_completed")


if __name__ == "__main__":
    asyncio.run(run_optimization_cycle())
