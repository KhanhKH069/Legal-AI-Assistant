import asyncio
import json as _json
import time as _time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Rate, Duration, Limiter

from src.core.config import config

# Default chat rate: config.max_requests_per_minute requests per minute
_chat_rate = Rate(config.max_requests_per_minute, Duration.MINUTE)
_chat_limiter = Limiter(_chat_rate)

from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from api.auth import get_current_user
from api.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

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


class ChatRequest(BaseModel):
    user_id: str
    message: str
    api_key: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    response: str
    intent: Optional[str] = None
    agent_name: Optional[str] = None
    user_id: str
    timestamp: str = ""


# Maps internal agent intent strings to friendly display names
_INTENT_LABELS: Dict[str, str] = {
    "STATUTORY": "Chuyên gia Pháp điển",
    "CASELAW": "Chuyên gia Án lệ",
    "OFFLINE": "Legal Assistant (Offline)",
}


@router.post(
    "", response_model=ChatResponse, dependencies=[Depends(RateLimiter(_chat_limiter))]
)
def chat_endpoint(payload: ChatRequest, request: Request) -> ChatResponse:
    user_id = payload.user_id
    graph = request.app.state.graph

    human_msg = HumanMessage(content=payload.message)
    _save_message(user_id, "user", payload.message)

    initial_state = {
        "messages": [human_msg],
        "next": "",
        "user_intent": "",
        "user_id": user_id,
        "user_info": {},
    }

    # The agent graph natively supports offline models based on config.enable_offline_mode

    try:
        config_dict = {"configurable": {"thread_id": user_id}}
        result = graph.invoke(initial_state, config=config_dict)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=500, detail="No response generated from agent")

    last_message = messages[-1]
    response_text = getattr(last_message, "content", str(last_message))

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


@router.get("/history/{user_id}", summary="Get Conversation History")
def get_chat_history(user_id: str) -> Dict:
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


@router.delete("/history/{user_id}", summary="Clear Conversation History")
def clear_chat_history(user_id: str) -> Dict:
    _clear_history(user_id)
    return {"user_id": user_id, "status": "cleared"}


@router.post(
    "/stream",
    summary="Streaming Chat (SSE)",
    dependencies=[Depends(RateLimiter(_chat_limiter))],
)
async def chat_stream_endpoint(
    payload: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    # Dùng employee_id hoặc username làm user_id để phân tách lịch sử chat
    user_id = current_user.employee_id or current_user.username
    human_msg = HumanMessage(content=payload.message)
    graph = request.app.state.graph

    async def event_generator():
        try:
            # The agent graph natively supports offline models based on config.enable_offline_mode
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
                async for event in graph.astream_events(
                    initial_state, config=config_dict, version="v2"
                ):
                    kind = event.get("event", "")
                    if kind == "on_chat_model_stream":
                        chunk_data = event.get("data", {})
                        chunk_msg = chunk_data.get("chunk")
                        if chunk_msg is not None:
                            token_text = getattr(chunk_msg, "content", "")
                            if isinstance(token_text, list):
                                token_text = " ".join(
                                    b.get("text", "") if isinstance(b, dict) else str(b)
                                    for b in token_text
                                )
                            if token_text:
                                full_text += token_text
                                payload_data: dict = {
                                    "token": token_text,
                                    "done": False,
                                    "type": "text",
                                }
                                if not intent_sent:
                                    payload_data["intent"] = intent_str
                                    intent_sent = True
                                yield f"data: {_json.dumps(payload_data)}\n\n"
                                await asyncio.sleep(0.01)

                    elif kind == "on_tool_start":
                        tool_name = event.get("name", "tool")
                        payload_data = {
                            "token": f"\n⏳ Đang tra cứu hệ thống ({tool_name})...\n",
                            "done": False,
                            "type": "tool_start",
                            "tool_name": tool_name,
                        }
                        yield f"data: {_json.dumps(payload_data)}\n\n"

                    elif kind == "on_tool_end":
                        tool_name = event.get("name", "tool")
                        payload_data = {
                            "token": f"✅ Đã tìm thấy kết quả từ {tool_name}.\n\n",
                            "done": False,
                            "type": "tool_end",
                            "tool_name": tool_name,
                        }
                        yield f"data: {_json.dumps(payload_data)}\n\n"

                    elif kind == "on_chain_end":
                        output = event.get("data", {}).get("output", {})
                        if isinstance(output, dict) and output.get("user_intent"):
                            intent_str = output["user_intent"]

            except Exception as stream_err:
                logger.warning(
                    "astream_events failed (%s) – falling back to invoke",
                    stream_err,
                )
                result = graph.invoke(initial_state, config=config_dict)
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


class GuestChatRequest(BaseModel):
    message: str
    session_id: str = "guest_anonymous"


@router.post(
    "/guest", tags=["Guest Chat"], dependencies=[Depends(RateLimiter(_chat_limiter))]
)
async def guest_chat(req: GuestChatRequest, request: Request):
    guest_graph = request.app.state.guest_graph
    human_msg = HumanMessage(content=req.message)
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
            else "Xin lỗi, tôi chưa thể trả lời câu hỏi pháp lý này. Vui lòng thử lại."
        )
    except Exception as e:
        logger.error("Guest chat error: %s", e)
        response_text = "Đã xảy ra lỗi. Vui lòng thử lại."

    return {
        "status": "ok",
        "response": response_text,
        "agent_name": "Legal Assistant",
        "session_id": req.session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/guest/stream",
    tags=["Guest Chat"],
    dependencies=[Depends(RateLimiter(_chat_limiter))],
)
async def guest_chat_stream(req: GuestChatRequest, request: Request):
    guest_graph = request.app.state.guest_graph
    # The guest graph natively supports offline models
    human_msg = HumanMessage(content=req.message)

    async def generate():
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
                else "Xin lỗi, tôi chưa thể trả lời câu hỏi này. Vui lòng liên hệ phapche@paraline.vn."
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
                    payload["intent"] = "STATUTORY"
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
