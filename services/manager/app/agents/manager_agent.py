from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.common.llm_provider import get_llm

REFINE_SYSTEM_PROMPT = """You are a request refiner for a code generation system.
Your job is to take a user's raw, possibly vague request and transform it into a clear,
specific, and actionable description for a Python code generator.

Rules:
- Keep the refined request concise but specific
- Add implicit requirements (e.g., error handling, input validation) if clearly needed
- Specify the expected output format if the user didn't
- Do NOT generate code yourself, only refine the request description
- Output ONLY the refined request text, nothing else"""


def build_refiner_chain():
    llm = get_llm(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", REFINE_SYSTEM_PROMPT),
        ("human", "Task type: {task_type}\nUser request: {user_input}"),
    ])
    return prompt | llm | StrOutputParser()
