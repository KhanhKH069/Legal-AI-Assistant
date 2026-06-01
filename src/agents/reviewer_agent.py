"""Reviewer Agent (Evaluator)"""

import json
from src.core.prompt_loader import get_prompt
from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import config


def reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    messages = state.get("messages", [])
    if not messages:
        return {"next": "pass"}

    # If offline, bypass
    if config.enable_offline_mode or not config.google_api_key:
        return {"next": "pass"}

    # Extract the user's original query
    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage) and not msg.content.startswith(
            "Feedback từ Trưởng phòng"
        ):
            user_query = msg.content
            break

    # The last message must be an AIMessage (the draft response)
    last_msg = messages[-1]
    if not isinstance(last_msg, AIMessage) or not last_msg.content:
        # If it's a tool call with no content, skip review
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return {"next": "pass"}
        return {"next": "pass"}

    draft_response = last_msg.content

    # Prevent infinite loop: Max 2 retries
    fail_count = sum(
        1
        for msg in messages
        if isinstance(msg, HumanMessage)
        and msg.content.startswith("Feedback từ Trưởng phòng")
    )
    if fail_count >= 2:
        return {"next": "pass"}

    llm = None
    if config.enable_offline_mode or not config.google_api_key:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model="qwen2.5:7b-instruct",
            temperature=0.1,
            base_url="http://localhost:11434",
        )
    else:
        llm = ChatGoogleGenerativeAI(
            model=config.model_name,
            google_api_key=config.google_api_key,
            temperature=0.1,
            max_tokens=config.max_tokens,
        )

    system_prompt_template = get_prompt("reviewer_agent")
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt_template)])

    try:
        chain = prompt | llm
        result = chain.invoke({"draft": draft_response, "query": user_query})

        # Parse JSON output from LLM
        content = result.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()

        data = json.loads(content)

        if data.get("status") == "FAIL":
            feedback = data.get("feedback", "Câu trả lời chưa đạt yêu cầu.")
            feedback_msg = HumanMessage(
                content=f"Feedback từ Trưởng phòng Pháp chế: {feedback}\nHãy viết lại câu trả lời và ghi nhớ feedback này."
            )

            # Trả về feedback để trigger workflow chạy lại
            return {"messages": [feedback_msg], "next": "fail"}

        return {"next": "pass"}
    except Exception as e:
        print(f"Reviewer Error: {e}")
        return {"next": "pass"}  # Fail open
