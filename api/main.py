import asyncio
import json as _json
import time as _time
import logging
import os
import shutil
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from api.routers import (
    applicants,
    files,
    job_requirements,
    screening,
    employees,
    attendance,
    helpdesk,
    benefits,
    notification,
    payroll,
    appraisal,
    skills,
    contracts,
    auth,
    audit,
    policies,
)
from src.db import init_db
from src.core.config import config
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_APP_VERSION = "1.0.0"
_startup_time: datetime | None = None


app = FastAPI(
    title="Paraline HR AI Agent API",
    version="1.0.0",
    description="FastAPI backend for HR multi-agent (LangGraph) assistant",
)

# Allow Next.js dev + prod origins; change to ["*"] for fully open access
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8501",  # Streamlit
    "http://127.0.0.1:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Simple in-process rate limiter (sliding window, per user_id) ──────────────
# Uses config.max_requests_per_minute (default: 10 req/min per user).
_rate_store: dict[str, list[float]] = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Sliding-window rate limiter on the /chat endpoint.

    Other endpoints (health, static assets) are not rate-limited so that
    monitoring tools don't get blocked.
    """
    if request.url.path.startswith("/chat") and request.method == "POST":
        # Identify caller by user_id query param or fallback to client IP
        user_key = request.query_params.get("user_id") or (
            request.client.host if request.client else "unknown"
        )
        now = time.time()
        window = _rate_store.setdefault(user_key, [])
        # Evict timestamps older than 60 s
        _rate_store[user_key] = [ts for ts in window if now - ts < 60]
        if len(_rate_store[user_key]) >= config.max_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "detail": (
                        f"Rate limit exceeded: max {config.max_requests_per_minute}"
                        " requests per minute. Please wait before retrying."
                    ),
                },
            )
        _rate_store[user_key].append(now)
    return await call_next(request)


# Routers for business resources
app.include_router(applicants.router)
app.include_router(screening.router)
app.include_router(job_requirements.router)
app.include_router(files.router)
app.include_router(employees.router)

# Routers for Odoo-inspired HR modules
app.include_router(attendance.router)
app.include_router(helpdesk.router)
app.include_router(benefits.router)
app.include_router(notification.router)
app.include_router(payroll.router)

# New Odoo-inspired modules (Phase 2)
app.include_router(appraisal.router)
app.include_router(skills.router)
app.include_router(contracts.router)
app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(policies.router)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and agent graph on startup."""
    global _startup_time
    _startup_time = datetime.now(timezone.utc)
    init_db()

    import subprocess
    import sys

    print("[ALEMBIC] Đang chạy Database Migrations tự động...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    except Exception as e:
        print(f"[ALEMBIC] Lỗi khi chạy migration: {e}")

    global graph
    global guest_graph
    if config.enable_offline_mode or not config.google_api_key:
        graph = None
        guest_graph = None
    else:
        from src.agents.orchestrator import (
            create_hr_agent_graph,
            create_guest_agent_graph,
        )

        graph = create_hr_agent_graph()
        guest_graph = create_guest_agent_graph()

    # ── LangSmith Tracing (optional, activates if LANGSMITH_API_KEY is set) ──
    import os

    _lskey = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if _lskey:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = _lskey
        os.environ["LANGCHAIN_PROJECT"] = os.getenv(
            "LANGCHAIN_PROJECT", "paraline-hr-agent"
        )
        logger.info(
            "LangSmith tracing enabled → project: %s", os.environ["LANGCHAIN_PROJECT"]
        )

    # ── LangChain LLM Cache (SQLite-backed, exact-match) ────────────────────
    if not config.enable_offline_mode:
        try:
            from langchain.globals import set_llm_cache
            from langchain_community.cache import SQLiteCache
            import pathlib

            pathlib.Path("data").mkdir(exist_ok=True)
            set_llm_cache(SQLiteCache(database_path="data/llm_cache.db"))
            logger.info("LangChain LLM cache enabled → data/llm_cache.db")
        except Exception as _e:
            logger.warning("LangChain cache not initialised: %s", _e)


# ── Conversation history helpers (SQLite-backed) ──────────────────────────────


def _load_history(user_id: str) -> List[BaseMessage]:
    """Load conversation history for a user from SQLite."""
    from api.database import engine
    from api.models import ConversationMessage
    from sqlmodel import Session, select as sql_select
    from langchain_core.messages import HumanMessage as HM, AIMessage as AM

    with Session(engine) as s:
        rows = s.exec(
            sql_select(ConversationMessage)
            .where(ConversationMessage.user_id == user_id)
            .order_by(ConversationMessage.id)
        ).all()
    return [
        HM(content=r.content) if r.role == "user" else AM(content=r.content)
        for r in rows
    ]


def _save_message(user_id: str, role: str, content: str):
    """Persist a single chat message to SQLite."""
    from api.database import engine
    from api.models import ConversationMessage
    from sqlmodel import Session

    with Session(engine) as s:
        s.add(
            ConversationMessage(
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )
        s.commit()


def _clear_history(user_id: str):
    """Delete all conversation messages for a user from SQLite."""
    from api.database import engine
    from api.models import ConversationMessage
    from sqlmodel import Session, select as sql_select

    with Session(engine) as s:
        rows = s.exec(
            sql_select(ConversationMessage).where(
                ConversationMessage.user_id == user_id
            )
        ).all()
        for r in rows:
            s.delete(r)
        s.commit()


graph = None  # type: ignore[var-annotated]


class ChatRequest(BaseModel):
    user_id: str
    message: str
    api_key: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    response: str
    intent: Optional[str] = None
    agent_name: Optional[str] = None  # Human-readable agent label (e.g. "CV Agent")
    user_id: str
    timestamp: str = ""


# Maps internal agent intent strings to friendly display names
_INTENT_LABELS: Dict[str, str] = {
    "POLICY_AGENT": "Policy Agent",
    "ONBOARD_AGENT": "Onboard Agent",
    "CV_AGENT": "CV Agent",
    "ANALYTICS_AGENT": "Analytics Agent",
    "ATTENDANCE_AGENT": "Attendance Agent",
    "HELPDESK_AGENT": "Helpdesk Agent",
    "BENEFITS_AGENT": "Benefits Agent",
    "APPRAISAL_AGENT": "Appraisal Agent",
    "OFFLINE": "Offline Agent",
}


@app.get("/health", summary="System Health Check")
def health_check() -> Dict:
    """Return rich system status including model, agents, and uptime."""
    uptime_seconds: float | None = None
    if _startup_time:
        delta = datetime.now(timezone.utc) - _startup_time
        uptime_seconds = round(delta.total_seconds(), 1)

    return {
        "status": "ok",
        "version": _APP_VERSION,
        "mode": "offline"
        if (config.enable_offline_mode or not config.google_api_key)
        else "online",
        "model": config.model_name if not config.enable_offline_mode else "offline-kb",
        "agents": [
            "policy_agent",
            "onboard_agent",
            "cv_agent",
            "analytics_agent",
            "attendance_agent",
            "helpdesk_agent",
            "benefits_agent",
            "appraisal_agent",
        ],
        "agent_count": 8,
        "graph_loaded": graph is not None,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    user_id = payload.user_id

    # History is now managed automatically by LangGraph checkpointer.
    # We still save to our custom SQL table for the history endpoint /chat/history
    human_msg = HumanMessage(content=payload.message)
    _save_message(user_id, "user", payload.message)

    initial_state = {
        "messages": [human_msg],
        "next": "",
        "user_intent": "",
        "user_id": user_id,
        "user_info": {},
    }

    if config.enable_offline_mode or not config.google_api_key:
        from src.agents.offline_agent import answer_question

        try:
            resp = answer_question(payload.message)
            _save_message(user_id, "assistant", resp)
            return ChatResponse(
                status="success",
                response=resp,
                intent="OFFLINE",
                agent_name="Offline Agent",
                user_id=user_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Offline agent error: {e}")

    try:
        config_dict = {"configurable": {"thread_id": user_id}}
        result = graph.invoke(initial_state, config=config_dict)  # type: ignore

        # Check if the graph is paused for human-in-the-loop
        current_state = graph.get_state(config_dict)
        if current_state.next and "attendance_sensitive_tools" in current_state.next:
            # The agent wants to call a sensitive tool, we must pause and ask for approval
            if current_state.values.get("messages"):
                last_msg = current_state.values["messages"][-1]
                if hasattr(last_msg, "tool_calls"):
                    pass

            return ChatResponse(
                status="requires_approval",
                response="Hệ thống cần bạn xác nhận để thực hiện tác vụ này (ví dụ: Xin nghỉ phép).",
                intent="ATTENDANCE_AGENT",
                agent_name="Attendance Agent",
                user_id=user_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=500, detail="No response generated from agent")

    last_message = messages[-1]
    response_text = getattr(last_message, "content", str(last_message))

    # If the response is a ToolMessage (happens when ToolNode -> END), format it
    if hasattr(last_message, "type") and last_message.type == "tool":
        response_text = f"Đã thực hiện xong: {last_message.content}"

    intent_str = result.get("user_intent", "")
    agent_label = _INTENT_LABELS.get(intent_str)
    if not agent_label:
        for key, label in _INTENT_LABELS.items():
            if key in intent_str:
                agent_label = label
                break

    _save_message(user_id, "assistant", response_text)

    return ChatResponse(
        status="success",
        response=response_text,
        intent=intent_str,
        agent_name=agent_label,
        user_id=user_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


class ApproveRequest(BaseModel):
    user_id: str
    approve: bool


@app.post(
    "/chat/approve", response_model=ChatResponse, summary="Approve/Reject paused action"
)
def chat_approve_endpoint(payload: ApproveRequest) -> ChatResponse:
    """Endpoint to resume a paused graph after human approval"""
    user_id = payload.user_id
    config_dict = {"configurable": {"thread_id": user_id}}

    current_state = graph.get_state(config_dict)
    if not current_state.next:
        raise HTTPException(status_code=400, detail="No action is pending approval")

    if payload.approve:
        # Resume the graph by passing None
        try:
            result = graph.invoke(None, config=config_dict)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error resuming graph: {e}")

        messages = result.get("messages", [])
        last_message = messages[-1]
        response_text = getattr(last_message, "content", str(last_message))

        # Format tool message if needed
        if hasattr(last_message, "type") and last_message.type == "tool":
            response_text = f"✅ Đã thực hiện thành công: {last_message.content}"

        _save_message(user_id, "assistant", response_text)

        return ChatResponse(
            status="success",
            response=response_text,
            intent="ATTENDANCE_AGENT",
            agent_name="Attendance Agent",
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    else:
        # User rejected. We need to clear the pending tool call or just update state.
        # For simplicity, we can just update the state to END or return a message.
        from langchain_core.messages import AIMessage

        graph.update_state(
            config_dict,
            {
                "messages": [
                    AIMessage(content="❌ Đã hủy thao tác theo yêu cầu của bạn.")
                ]
            },
            as_node="attendance_agent",
        )

        _save_message(user_id, "assistant", "❌ Đã hủy thao tác theo yêu cầu của bạn.")

        return ChatResponse(
            status="success",
            response="❌ Đã hủy thao tác theo yêu cầu của bạn.",
            intent="ATTENDANCE_AGENT",
            agent_name="Attendance Agent",
            user_id=user_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@app.get("/chat/history/{user_id}", summary="Get Conversation History")
def get_chat_history(user_id: str) -> Dict:
    """Return the full conversation history for a given user_id from SQLite."""
    history = _load_history(user_id)
    messages = []
    for msg in history:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        messages.append({"role": role, "content": msg.content})
    return {
        "user_id": user_id,
        "message_count": len(messages),
        "messages": messages,
    }


@app.delete("/chat/history/{user_id}", summary="Clear Conversation History")
def clear_chat_history(user_id: str) -> Dict:
    """Clear the conversation history for a user from SQLite."""
    _clear_history(user_id)
    return {"user_id": user_id, "status": "cleared"}


@app.post("/chat/stream", summary="Streaming Chat (SSE)")
async def chat_stream_endpoint(payload: ChatRequest):
    """Server-Sent Events streaming version of /chat.

    Returns text/event-stream with incremental tokens so the UI can display
    the response word-by-word (like ChatGPT).
    - Offline mode: streams from local KB answer word-by-word with delay
    - Online mode:  uses graph.astream_events() for native Gemini token streaming
    """
    user_id = payload.user_id
    human_msg = HumanMessage(content=payload.message)

    async def event_generator():
        try:
            # ── Offline mode ──────────────────────────────────────────────
            if config.enable_offline_mode or not config.google_api_key:
                from src.agents.offline_agent import answer_question

                full_resp = answer_question(payload.message)
                _save_message(user_id, "user", payload.message)
                _save_message(user_id, "assistant", full_resp)

                words = full_resp.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    data = _json.dumps({"token": chunk, "done": False})
                    yield f"data: {data}\n\n"
                    await asyncio.sleep(0.03)

            # ── Online mode: native streaming via astream_events ──────────
            else:
                _save_message(user_id, "user", payload.message)
                initial_state = {
                    "messages": [human_msg],
                    "next": "",
                    "user_intent": "",
                    "user_id": user_id,
                    "user_info": {},
                }
                config_dict = {"configurable": {"thread_id": user_id}}
                _t0 = _time.perf_counter()

                full_text = ""
                intent_sent = False
                intent_str = ""

                try:
                    # Use astream_events v2 to get real token-level chunks from Gemini
                    async for event in graph.astream_events(  # type: ignore[union-attr]
                        initial_state, config=config_dict, version="v2"
                    ):
                        kind = event.get("event", "")
                        # on_chat_model_stream fires for each LLM token chunk
                        if kind == "on_chat_model_stream":
                            chunk_data = event.get("data", {})
                            chunk_msg = chunk_data.get("chunk")
                            if chunk_msg is not None:
                                token_text = getattr(chunk_msg, "content", "")
                                if isinstance(token_text, list):
                                    # Gemini sometimes returns list of content blocks
                                    token_text = " ".join(
                                        b.get("text", "")
                                        if isinstance(b, dict)
                                        else str(b)
                                        for b in token_text
                                    )
                                if token_text:
                                    full_text += token_text
                                    payload_data: dict = {
                                        "token": token_text,
                                        "done": False,
                                    }
                                    if not intent_sent:
                                        payload_data["intent"] = intent_str
                                        intent_sent = True
                                    yield f"data: {_json.dumps(payload_data)}\n\n"

                        # Capture intent from graph state updates
                        elif kind == "on_chain_end":
                            output = event.get("data", {}).get("output", {})
                            if isinstance(output, dict) and output.get("user_intent"):
                                intent_str = output["user_intent"]

                except Exception as stream_err:
                    # Fallback: run synchronously if astream_events fails
                    logger.warning(
                        "astream_events failed (%s) – falling back to invoke",
                        stream_err,
                    )
                    result = graph.invoke(initial_state, config=config_dict)  # type: ignore
                    messages = result.get("messages", [])
                    last_msg = messages[-1] if messages else None
                    full_text = getattr(last_msg, "content", "") if last_msg else ""
                    intent_str = result.get("user_intent", "")
                    if isinstance(full_text, list):
                        full_text = " ".join(
                            b.get("text", "") if isinstance(b, dict) else str(b)
                            for b in full_text
                        )
                    words = str(full_text).split(" ")
                    for i, word in enumerate(words):
                        chunk = word + (" " if i < len(words) - 1 else "")
                        yield f"data: {_json.dumps({'token': chunk, 'done': False, 'intent': intent_str if i == 0 else None})}\n\n"
                        await asyncio.sleep(0.02)

                _resp_ms = (_time.perf_counter() - _t0) * 1000
                _save_message(user_id, "assistant", full_text)

                # Check HITL pause
                try:
                    current_state = graph.get_state(config_dict)  # type: ignore
                    if (
                        current_state.next
                        and "attendance_sensitive_tools" in current_state.next
                    ):
                        pause_msg = "Hệ thống cần bạn xác nhận để thực hiện tác vụ này (ví dụ: Xin nghỉ phép)."
                        yield f"data: {_json.dumps({'token': pause_msg, 'done': False})}\n\n"
                except Exception:
                    pass

                # Record metrics
                agent_label = _INTENT_LABELS.get(intent_str.strip().upper())
                if not agent_label:
                    for key, label in _INTENT_LABELS.items():
                        if key in intent_str.upper():
                            agent_label = label
                            break
                from src.services.metrics import get_metrics_collector

                get_metrics_collector().record(
                    user_id=user_id,
                    agent_name=agent_label or "Unknown Agent",
                    response_time_ms=_resp_ms,
                    message_preview=payload.message,
                )

            # Done signal
            yield f"data: {_json.dumps({'token': '', 'done': True})}\n\n"

        except Exception as e:
            import traceback

            traceback.print_exc()
            yield f"data: {_json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/metrics/summary", tags=["Metrics"], summary="AI Performance Metrics")
def metrics_summary() -> Dict:
    """Return real-time AI performance metrics: agent usage, response times, cache stats."""
    from src.services.metrics import get_metrics_collector

    return get_metrics_collector().get_summary()


@app.get("/payroll/tax-calculator", summary="VN Income Tax Calculator")
def vn_tax_calculator(gross_vnd: float, dependents: int = 0) -> Dict:
    """Calculate VN Personal Income Tax (TNCN) for a gross salary.

    Uses official 7-bracket progressive table (Circular 111/2013, updated 2024).
    """
    from src.tools.payroll_tools import (
        _calculate_vn_pit,
        _PERSONAL_DEDUCTION_VND,
        _DEPENDENT_DEDUCTION_VND,
    )

    bhxh = gross_vnd * 0.08
    bhyt = gross_vnd * 0.015
    bhtn = gross_vnd * 0.01
    insurance = bhxh + bhyt + bhtn
    personal_ded = _PERSONAL_DEDUCTION_VND
    dependent_ded = dependents * _DEPENDENT_DEDUCTION_VND
    taxable = max(gross_vnd - insurance - personal_ded - dependent_ded, 0)
    pit = _calculate_vn_pit(taxable)
    net = gross_vnd - insurance - pit

    return {
        "gross_vnd": gross_vnd,
        "dependents": dependents,
        "bhxh_vnd": round(bhxh),
        "bhyt_vnd": round(bhyt),
        "bhtn_vnd": round(bhtn),
        "total_insurance_vnd": round(insurance),
        "personal_deduction": personal_ded,
        "dependent_deduction": dependent_ded,
        "taxable_income_vnd": round(taxable),
        "income_tax_vnd": round(pit),
        "net_salary_vnd": round(net),
        "effective_tax_rate": round(pit / gross_vnd * 100, 2) if gross_vnd > 0 else 0,
    }


# ── Guest Chat Endpoints (no auth required) ───────────────────────────────────


class GuestChatRequest(BaseModel):
    message: str
    session_id: str = "guest_anonymous"  # client-generated session ID


guest_graph = None  # initialized in on_startup


@app.post("/chat/guest", tags=["Guest Chat"])
async def guest_chat(req: GuestChatRequest):
    """Chat endpoint for unauthenticated guests / applicants.

    Only recruitment-related queries are handled.  No employee data is exposed.
    """
    from src.agents.offline_agent import answer_question
    from langchain_core.messages import HumanMessage

    human_msg = HumanMessage(content=req.message)

    # Offline mode — use a restricted offline response
    if guest_graph is None:
        # Prepend guest context to message
        guest_query = f"[GUEST/ỨNG VIÊN HỎI] {req.message}"
        answer = answer_question(guest_query)
        return {
            "status": "ok",
            "response": answer,
            "agent_name": "Recruitment Assistant",
            "session_id": req.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        initial_state = {
            "messages": [human_msg],
            "next": "",
            "user_intent": "",
            "session_id": req.session_id,
        }
        result = guest_graph.invoke(initial_state)
        messages = result.get("messages", [])
        last = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        response_text = (
            last.content
            if last
            else "Xin lỗi, tôi chưa thể trả lời câu hỏi này. Vui lòng liên hệ hr@paraline.vn."
        )
    except Exception as e:
        logger.error("Guest chat error: %s", e)
        response_text = "Đã xảy ra lỗi. Vui lòng thử lại hoặc liên hệ hr@paraline.vn."

    return {
        "status": "ok",
        "response": response_text,
        "agent_name": "Recruitment Assistant",
        "session_id": req.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/chat/guest/stream", tags=["Guest Chat"])
async def guest_chat_stream(req: GuestChatRequest):
    """SSE streaming chat for unauthenticated guests / applicants."""
    from src.agents.offline_agent import answer_question
    from langchain_core.messages import HumanMessage

    human_msg = HumanMessage(content=req.message)

    async def generate():
        if guest_graph is None:
            # Offline fallback
            guest_query = f"[GUEST/ỨNG VIÊN HỎI] {req.message}"
            answer = answer_question(guest_query)
            words = answer.split(" ")
            for i, word in enumerate(words):
                chunk = _json.dumps(
                    {
                        "token": word + (" " if i < len(words) - 1 else ""),
                        "done": False,
                        "intent": "RECRUITMENT",
                    }
                )
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.03)
        else:
            try:
                initial_state = {
                    "messages": [human_msg],
                    "next": "",
                    "user_intent": "",
                    "session_id": req.session_id,
                }
                result = guest_graph.invoke(initial_state)
                messages = result.get("messages", [])
                last = next(
                    (m for m in reversed(messages) if isinstance(m, AIMessage)), None
                )
                full_text = (
                    last.content
                    if last
                    else "Xin lỗi, tôi chưa thể trả lời câu hỏi này. Vui lòng liên hệ hr@paraline.vn."
                )
                if isinstance(full_text, list):
                    text_parts = []
                    for block in full_text:
                        if isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                        elif isinstance(block, str):
                            text_parts.append(block)
                    full_text = " ".join(text_parts)

                words = str(full_text).split(" ")
                for i, word in enumerate(words):
                    payload: dict = {
                        "token": word + (" " if i < len(words) - 1 else ""),
                        "done": False,
                    }
                    if i == 0:
                        payload["intent"] = "RECRUITMENT"
                    yield f"data: {_json.dumps(payload)}\n\n"
                    await asyncio.sleep(0.025)
            except Exception as e:
                logger.error("Guest stream error: %s", e)
                err = _json.dumps(
                    {"token": "Đã xảy ra lỗi. Vui lòng thử lại.", "done": False}
                )
                yield f"data: {err}\n\n"

        yield f"data: {_json.dumps({'token': '', 'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/upload_cv", tags=["Guest Chat"])
async def upload_cv(file: UploadFile = File(...)):
    """Upload a CV file to the system for analysis."""
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ định dạng PDF.")

    # Ensure directory exists
    os.makedirs("data/cv_uploads", exist_ok=True)

    # Save the file
    file_path = os.path.join("data/cv_uploads", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "success", "file_path": file_path, "filename": file.filename}


# Mount static files for frontend UI
# Important: Do this at the end so it doesn't override API routes
public_path = pathlib.Path(__file__).parent.parent / "public"
app.mount("/app", StaticFiles(directory=str(public_path), html=True), name="static")
