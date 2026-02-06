import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.common.llm_provider import get_llm
from services.common.logging_utils import setup_logger

logger = setup_logger("evaluator.agent")

EVALUATOR_SYSTEM_PROMPT = """You are a code quality evaluator. Given a user request and the generated code output,
score the output on three dimensions (each 0-10):

1. **Relevance**: Does the code address what the user asked for?
2. **Quality**: Is the code well-structured, readable, and likely to work correctly?
3. **Safety**: Is the code free from security issues, hardcoded secrets, and dangerous operations?

Respond in EXACTLY this JSON format (no extra text):
{{"relevance": <0-10>, "quality": <0-10>, "safety": <0-10>, "reasoning": "<brief explanation>"}}"""


def build_evaluator_chain():
    llm = get_llm(temperature=0.1)
    prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATOR_SYSTEM_PROMPT),
        ("human", "User request: {user_input}\n\nRefined request: {refined_input}\n\nGenerated code:\n{worker_output}"),
    ])
    return prompt | llm | StrOutputParser()


async def evaluate_with_llm(user_input: str, refined_input: str, worker_output: str) -> dict:
    """LLM-based evaluation. Returns {score: 0-1, details: {...}}."""
    chain = build_evaluator_chain()
    raw = await chain.ainvoke({
        "user_input": user_input,
        "refined_input": refined_input,
        "worker_output": worker_output,
    })

    try:
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(raw)

        relevance = min(max(parsed.get("relevance", 5), 0), 10) / 10
        quality = min(max(parsed.get("quality", 5), 0), 10) / 10
        safety = min(max(parsed.get("safety", 5), 0), 10) / 10
        reasoning = parsed.get("reasoning", "")

        # Weighted average: relevance 40%, quality 35%, safety 25%
        score = relevance * 0.4 + quality * 0.35 + safety * 0.25

        return {
            "score": round(score, 3),
            "details": {
                "relevance": relevance,
                "quality": quality,
                "safety": safety,
                "reasoning": reasoning,
            },
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("llm_eval_parse_failed", extra={"error": str(e), "raw": raw[:200]})
        return {"score": 0.5, "details": {"parse_error": str(e), "raw": raw[:200]}}
