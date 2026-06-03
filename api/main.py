import logging
import os
from datetime import datetime, timezone

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.routers import (
    auth,
    audit,
    chat,
    document_review,
    stt,
)
from src.db import init_db
from src.core.config import config

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


    import subprocess
    import sys

    logger = logging.getLogger("api")

    print("[ALEMBIC] Đang chạy Database Migrations tự động...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    except Exception as e:
        print(f"[ALEMBIC] Lỗi khi chạy migration: {e}")

    try:
        import redis.asyncio as redis_async
        from fastapi_limiter import FastAPILimiter
        _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_conn = redis_async.from_url(_redis_url, encoding="utf8", decode_responses=True)
        await FastAPILimiter.init(redis_conn)
        print("✅ Rate Limiter (Redis) enabled")
    except ImportError:
        print("Rate Limiter: fastapi_limiter not available, skipping")
    except Exception as e:
        print(f"Failed to init Rate Limiter: {e}")

    if config.enable_offline_mode or not config.google_api_key:
        app.state.graph = None
        app.state.guest_graph = None

        logger.info("Offline mode enabled, LLM caching disabled.")
    else:
        from src.agents.orchestrator import create_legal_agent_graph
        from src.agents.guest_orchestrator import create_guest_agent_graph
        from langchain_core.globals import set_llm_cache
        from langchain_community.cache import RedisSemanticCache
        from langchain_community.embeddings import HuggingFaceEmbeddings

        app.state.graph = create_legal_agent_graph()
        app.state.guest_graph = create_guest_agent_graph()

        try:
            set_llm_cache(
                RedisSemanticCache(
                    redis_url=config.redis_url,
                    embedding=HuggingFaceEmbeddings(
                        model_name="paraphrase-multilingual-MiniLM-L12-v2"
                    ),
                    score_threshold=0.15,
                )
            )
            print("✅ Redis Semantic Cache Enabled")
        except Exception as e:
            print(f"⚠️ Failed to enable Semantic Cache: {e}")

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

    if not config.enable_offline_mode:
        try:
            from langchain_core.globals import set_llm_cache
            from langchain_community.cache import RedisCache
            import redis
            import os

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.Redis.from_url(redis_url)
            set_llm_cache(RedisCache(redis_=redis_client))
            logger.info(f"LangChain LLM cache enabled (Redis) → {redis_url}")
        except Exception as _e:
            logger.warning("LangChain cache not initialised: %s", _e)

    yield


app = FastAPI(
    title="Legal AI Assistant API",
    version="1.0.0",
    description="FastAPI backend for Vietnamese Legal AI Agent (LangGraph) — Pháp điển + Án lệ",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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



