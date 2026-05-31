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
    chat,
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
    else:
        from src.agents.orchestrator import create_hr_agent_graph
        from src.agents.guest_orchestrator import create_guest_agent_graph

        app.state.graph = create_hr_agent_graph()
        app.state.guest_graph = create_guest_agent_graph()

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
    title="Paraline HR AI Agent API",
    version="1.0.0",
    description="FastAPI backend for HR multi-agent (LangGraph) assistant",
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
app.include_router(chat.router)


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
