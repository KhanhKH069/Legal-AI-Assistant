from typing import Dict, List, Optional

# Thêm cấu hình CORS
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from api.routers import applicants, files, job_requirements, screening
from src.agents.orchestrator import create_hr_agent_graph
from src.db import init_db
from src.core.config import config


app = FastAPI(
    title="Paraline HR AI Agent API",
    version="1.0.0",
    description="FastAPI backend for HR multi-agent (LangGraph) assistant",
)

# Cho phép mọi origin (hoặc chỉnh lại allow_origins=["http://localhost:3000"] nếu muốn an toàn hơn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers for business resources
app.include_router(applicants.router)
app.include_router(screening.router)
app.include_router(job_requirements.router)
app.include_router(files.router)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and agent graph on startup."""
    init_db()
    global graph
    graph = create_hr_agent_graph()

ConversationStore = Dict[str, List[BaseMessage]]
conversation_history: ConversationStore = {}


class ChatRequest(BaseModel):
    user_id: str
    message: str
    api_key: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    response: str
    intent: Optional[str] = None
    user_id: str


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    user_id = payload.user_id

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    human_msg = HumanMessage(content=payload.message)
    conversation_history[user_id].append(human_msg)

    initial_state = {
        "messages": conversation_history[user_id],
        "next": "",
        "user_intent": "",
        "user_id": user_id,
        "user_info": {},
    }

    # if offline mode is enabled or we don't have an API key, bypass the graph
    # and answer locally.  this lets the service work purely from the
    # project files.
    if config.enable_offline_mode or not config.google_api_key:
        from src.agents.offline_agent import answer_question
        try:
            resp = answer_question(payload.message)
            conversation_history[user_id].append(AIMessage(content=resp))
            return ChatResponse(status="success", response=resp, intent="OFFLINE", user_id=user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Offline agent error: {e}")

    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=500, detail="No response generated from agent")

    last_message = messages[-1]

    response_text = getattr(last_message, "content", str(last_message))

    conversation_history[user_id].append(AIMessage(content=response_text))

    return ChatResponse(
        status="success",
        response=response_text,
        intent=result.get("user_intent", ""),
        user_id=user_id,
    )

