from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.common.llm_provider import get_llm


def build_worker_chain(system_prompt: str):
    """Build a LangChain chain with dynamically loaded system prompt."""
    llm = get_llm(temperature=0.3)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{refined_input}"),
    ])
    return prompt | llm | StrOutputParser()
