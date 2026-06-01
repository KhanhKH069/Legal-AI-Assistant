import asyncio
import json as _json
import time as _time
import logging
import os
import shutil
import pathlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from api.routers import (
    auth,
    audit,
    chat,
    document_review,
    stt,
)
from src.db import init_db
from src.core.config import config
import time

from src.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

_APP_VERSION = "1.0.0"
_startup_time: datetime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and agent graph on startup."""
    global _startup_time
    _startup_time = datetime.now(timezone.utc)
    init_db()

    # Rate limiting is now handled per-router (e.g. in chat.py) via pyrate_limiter in fastapi-limiter>=0.2.0

    import subprocess
    import sys

    print("[ALEMBIC] Đang chạy Database Migrations tự động...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    except Exception as e:
        print(f"[ALEMBIC] Lỗi khi chạy migration: {e}")

    if config.enable_offline_mode or not config.google_api_key:
        app.state.graph = None
        app.state.guest_graph = None

        # Enable Semantic Cache
        import logging

        logger = logging.getLogger("api")
        logger.info("Offline mode enabled, LLM caching disabled.")
    else:
        from src.agents.orchestrator import create_legal_agent_graph
        from src.agents.guest_orchestrator import create_guest_agent_graph
        from langchain.globals import set_llm_cache
        from langchain_community.cache import RedisSemanticCache
        from langchain_community.embeddings import HuggingFaceEmbeddings

        app.state.graph = create_legal_agent_graph()
        app.state.guest_graph = create_guest_agent_graph()

        try:
            # Semantic Caching
            set_llm_cache(
                RedisSemanticCache(
                    redis_url=config.redis_url,
                    embedding=HuggingFaceEmbeddings(
                        model_name="paraphrase-multilingual-MiniLM-L12-v2"
                    ),
                    score_threshold=0.15,  # lower distance means higher similarity (depends on distance metric, usually L2)
                )
            )
            print("✅ Redis Semantic Cache Enabled")
        except Exception as e:
            print(f"⚠️ Failed to enable Semantic Cache: {e}")

    # ── LangSmith Tracing (optional, activates if LANGSMITH_API_KEY is set) ──
    import os

    _lskey = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if _lskey:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = _lskey
        os.environ["LANGCHAIN_PROJECT"] = os.getenv(
            "LANGCHAIN_PROJECT", "legal-ai-assistant"
        )
        logger.info(
            "LangSmith tracing enabled → project: %s", os.environ["LANGCHAIN_PROJECT"]
        )

    # ── LangChain LLM Cache (Redis-backed) ─────────────────
    if not config.enable_offline_mode:
        try:
            from langchain.globals import set_llm_cache
            from langchain_community.cache import RedisCache
            import redis
            import os

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.Redis.from_url(redis_url)
            set_llm_cache(RedisCache(redis_=redis_client))
            logger.info(f"LangChain LLM cache enabled (Redis) → {redis_url}")
        except Exception as _e:
            logger.warning("LangChain cache not initialised: %s", _e)

    yield  # Application runs here
    # Shutdown logic (if any) goes after yield


app = FastAPI(
    title="Legal AI Assistant API",
    version="1.0.0",
    description="FastAPI backend for Vietnamese Legal AI Agent (LangGraph) — Pháp điển + Án lệ",
    lifespan=lifespan,
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


# Core routers (auth + chat — used by Legal AI)
app.include_router(auth.router)
app.include_router(audit.router)
app.include_router(chat.router)
app.include_router(document_review.router)
app.include_router(stt.router, prefix="/api", tags=["Speech-to-Text"])


from src.services.metrics import get_metrics_collector


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "version": _APP_VERSION}


@app.get("/metrics/summary", tags=["Metrics"])
def get_metrics_summary():
    return get_metrics_collector().get_summary()


# Mount static files for frontend UI
# Important: Do this at the end so it doesn't override API routes
public_path = pathlib.Path(__file__).parent.parent / "public"
app.mount("/app", StaticFiles(directory=str(public_path), html=True), name="static")
