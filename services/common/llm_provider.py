from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from services.common.config import get_settings


def _build_mock_llm() -> BaseChatModel:
    """Build a mock LLM for testing without an API key."""
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, BaseMessage
    from langchain_core.outputs import ChatResult, ChatGeneration
    from typing import Any, Optional

    class MockChatModel(BaseChatModel):
        """Mock LLM that returns context-aware responses."""

        @property
        def _llm_type(self) -> str:
            return "mock"

        def _generate(
            self,
            messages: list[BaseMessage],
            stop: Optional[list[str]] = None,
            run_manager: Any = None,
            **kwargs: Any,
        ) -> ChatResult:
            last_msg = messages[-1].content.lower() if messages else ""

            # Detect context: evaluator, optimizer-analyzer, optimizer-patcher, refiner, or worker
            all_text = " ".join(m.content for m in messages).lower()

            if "score" in all_text and "relevance" in all_text and "quality" in all_text:
                # Evaluator agent — detect bad output
                if "hello world" in all_text and "def " not in all_text:
                    response = '{"relevance": 1, "quality": 1, "safety": 5, "reasoning": "Output is just hello world, not actual code. Completely irrelevant to the request."}'
                else:
                    response = '{"relevance": 8, "quality": 7, "safety": 9, "reasoning": "The code correctly implements the requested functionality with clean structure."}'
            elif "failure_patterns" in all_text and "root_causes" in all_text:
                # Optimizer analyzer
                response = '{"failure_patterns": ["Output not matching expected code format", "Missing error handling"], "root_causes": ["Prompt lacks specificity about output format", "No instruction for error handling"], "improvement_suggestions": ["Add explicit output format instructions", "Include error handling requirements", "Specify coding best practices"]}'
            elif "improved version" in all_text or "improve a system prompt" in all_text:
                # Optimizer patcher
                response = (
                    "You are an expert Python code generator. Given a user request, generate clean, "
                    "well-structured, working Python code.\n\n"
                    "Requirements:\n"
                    "- Include proper error handling with try/except blocks\n"
                    "- Add type hints to function signatures\n"
                    "- Include brief docstrings for functions\n"
                    "- Follow PEP 8 style guidelines\n"
                    "- Include input validation where appropriate\n"
                    "- Return ONLY the code block, no extra explanation."
                )
            elif "request refiner" in all_text or "refine" in all_text:
                # Manager refiner
                response = (
                    "Write a well-structured Python function that implements the requested functionality. "
                    "Include proper error handling, type hints, and a brief docstring. "
                    "The function should handle edge cases and validate inputs."
                )
            else:
                # Worker agent — detect bad prompt
                if "just say hello world" in all_text:
                    response = "Hello World"
                else:
                    response = (
                        "def solution(data):\n"
                        '    """Implements the requested functionality."""\n'
                        "    if not data:\n"
                        "        raise ValueError('Input data cannot be empty')\n"
                        "    result = []\n"
                        "    for item in data:\n"
                        "        result.append(item)\n"
                        "    return result\n"
                    )

            message = AIMessage(content=response)
            return ChatResult(generations=[ChatGeneration(message=message)])

    return MockChatModel()


def get_llm(temperature: float = 0.3) -> BaseChatModel:
    settings = get_settings()

    if settings.LLM_PROVIDER == "gemini":
        if not settings.LLM_API_KEY:
            # Fall back to mock when no API key is provided
            return _build_mock_llm()
        return ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.LLM_API_KEY,
            temperature=temperature,
        )
    elif settings.LLM_PROVIDER == "mock":
        return _build_mock_llm()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
