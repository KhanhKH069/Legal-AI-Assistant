"""
Hallucination Guardrail Service
Takes the retrieved context and synthesizes a grounded answer,
preventing hallucination (fabrication) of facts.
"""

from typing import Dict, Any
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from src.core.config import config


def guardrail_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guardrail node for LangGraph.
    Runs after policy_tools. It takes the retrieved context (from ToolMessage)
    and the original user query, then uses a strict prompt to generate an answer.
    """
    messages = state.get("messages", [])
    if not messages:
        return state

    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_query = msg.content

    context = ""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            context = msg.content
            break

    if not context:
        return state

    if config.enable_offline_mode or not config.google_api_key:
        return state

    from src.core.llm import get_llm
    llm = get_llm(temperature=0.0)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a strict HR Legal Assistant.
Your task is to answer the user's query using ONLY the provided <context>.

RULES:
1. DO NOT fabricate or hallucinate any information.
2. If the answer is not in the context, explicitly say: "Xin lỗi, tôi không tìm thấy thông tin trong tài liệu nội bộ."
3. If you find the answer, append the source citation at the end of your response based on the context.
4. Respond in Vietnamese.

<context>
{context}
</context>
""",
            ),
            ("user", "{query}"),
        ]
    )

    chain = prompt | llm

    try:
        response = chain.invoke({"context": context, "query": user_query})

        return {
            "messages": [response],
            "next": "end",
            "user_intent": state.get("user_intent", ""),
            "user_id": state.get("user_id", ""),
            "user_info": state.get("user_info", {}),
        }
    except Exception as e:
        print(f"Guardrail error: {e}")
        return state
