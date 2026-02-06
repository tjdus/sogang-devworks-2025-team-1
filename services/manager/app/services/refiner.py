from services.manager.app.agents.manager_agent import build_refiner_chain
from services.common.logging_utils import setup_logger

logger = setup_logger("manager.refiner")


async def refine_request(user_input: str, task_type: str) -> str:
    chain = build_refiner_chain()
    refined = await chain.ainvoke({"user_input": user_input, "task_type": task_type})
    logger.info("refined_request", extra={"original": user_input[:100], "refined": refined[:100]})
    return refined
