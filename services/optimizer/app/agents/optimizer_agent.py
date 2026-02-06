import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.common.llm_provider import get_llm
from services.common.logging_utils import setup_logger

logger = setup_logger("optimizer.agent")

ANALYZER_PROMPT = """You are a prompt engineering expert analyzing failures in an AI code generation system.

Given the current system prompt and a list of failed executions (with user inputs, outputs, and evaluation details),
identify the root causes of failure and suggest specific improvements to the system prompt.

Respond in EXACTLY this JSON format:
{{
    "failure_patterns": ["pattern1", "pattern2"],
    "root_causes": ["cause1", "cause2"],
    "improvement_suggestions": ["suggestion1", "suggestion2"]
}}"""

PATCHER_PROMPT = """You are a prompt engineering expert. Your job is to improve a system prompt for an AI code generator.

Current system prompt:
{current_prompt}

Analysis of recent failures:
{failure_analysis}

Specific improvement suggestions:
{suggestions}

Write an IMPROVED version of the system prompt that addresses the identified issues.
Output ONLY the new system prompt text, nothing else. Do not wrap it in quotes or markdown."""


def build_analyzer_chain():
    llm = get_llm(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", ANALYZER_PROMPT),
        ("human", "Current system prompt:\n{current_prompt}\n\nFailed executions:\n{failure_logs}"),
    ])
    return prompt | llm | StrOutputParser()


def build_patcher_chain():
    llm = get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a prompt engineering expert."),
        ("human", PATCHER_PROMPT),
    ])
    return prompt | llm | StrOutputParser()


async def analyze_failures(current_prompt: str, failure_logs: list[dict]) -> dict:
    """Analyze failure patterns using LLM."""
    chain = build_analyzer_chain()
    logs_text = json.dumps(failure_logs[:10], indent=2, default=str)  # Limit to 10 logs

    raw = await chain.ainvoke({
        "current_prompt": current_prompt,
        "failure_logs": logs_text,
    })

    try:
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("analysis_parse_failed", extra={"raw": raw[:200]})
        return {
            "failure_patterns": ["Unable to parse analysis"],
            "root_causes": ["Analysis parsing failed"],
            "improvement_suggestions": ["Add more specific instructions to the prompt"],
        }


async def generate_improved_prompt(current_prompt: str, failure_analysis: dict) -> str:
    """Generate an improved system prompt based on failure analysis."""
    chain = build_patcher_chain()
    suggestions = "\n".join(f"- {s}" for s in failure_analysis.get("improvement_suggestions", []))

    improved = await chain.ainvoke({
        "current_prompt": current_prompt,
        "failure_analysis": json.dumps(failure_analysis, indent=2),
        "suggestions": suggestions,
    })

    return improved.strip()
