from src.core.config import config
from langchain_core.messages import HumanMessage
import sys

sys.stdout.reconfigure(encoding="utf-8")


def test_chatbot():
    # Force online mode to use Gemini
    config.enable_offline_mode = False

    # Must import AFTER setting config to initialize LLM
    from src.agents.orchestrator import create_guest_agent_graph

    print("=== HR AI Chatbot Tester ===")
    graph = create_guest_agent_graph()
    user_id = "test_user_001"

    questions = [
        "Chào HR, mình vừa gửi CV lên vị trí AI Engineer Intern, nếu pass thì bao lâu mình được báo kết quả?",
        "À mình muốn hỏi thêm về phúc lợi, công ty có chế độ làm remote không?",
    ]

    config_dict = {"configurable": {"thread_id": user_id}}

    for q in questions:
        print(f"\n[USER]: {q}")
        response = graph.invoke(
            {"messages": [HumanMessage(content=q)], "user_id": user_id},
            config=config_dict,
        )

        # Output the final message from the agent
        ai_message = response["messages"][-1].content
        print(f"[AI]: {ai_message}")


if __name__ == "__main__":
    test_chatbot()
