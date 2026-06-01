"""Configuration Management - Gemini API
# Triggering reload
"""

import os
from dotenv import load_dotenv

# automatically load .env from project root; override existing environment vars
load_dotenv(override=True)


class Config:
    """Application configuration for Gemini"""

    def __init__(self):
        # Gemini API Configuration
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        # set a valid model name for the Google Generative AI API
        # Use environment model or default to gemini-2.5-flash
        self.model_name = os.getenv("MODEL_NAME", "gemini-2.5-flash")
        # Feature Flags
        self.enable_analytics = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        self.enable_audit_log = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
        # when true, chat requests are answered using a built-in knowledge base
        # derived from local markdown files instead of calling an LLM
        self.enable_offline_mode = os.getenv("OFFLINE_MODE", "false").lower() == "true"

        # debug: print resolved model on startup (only if actually using Gemini)
        if self.enable_offline_mode or not self.google_api_key:
            mode_desc = "offline mode" if self.enable_offline_mode else "no API key"
            print(f"[CONFIG] {mode_desc} – Gemini calls will be skipped")
        else:
            print(f"[CONFIG] using Gemini model: {self.model_name}")
        self.temperature = float(os.getenv("TEMPERATURE", "0.0"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))

        # Gateway Configuration
        self.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))

        # Database Configuration
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite:///data/sql_db/legal_agent.db"
        )
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        self.chromadb_port = int(os.getenv("CHROMADB_PORT", "8000"))
        self.chromadb_dir = os.getenv("CHROMADB_DIR", "./chroma_db")

        # Legal AI collection names
        self.statutory_collection = os.getenv("STATUTORY_COLLECTION", "legal_statutory")
        self.caselaw_collection = os.getenv("CASELAW_COLLECTION", "legal_caselaw")

        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "data/logs/app.log")

    def validate(self) -> bool:
        """Validate configuration.

        The API key is only mandatory when offline mode is disabled; if
        `enable_offline_mode` is True we can run without a key because all
        responses are generated locally.
        """
        if not self.google_api_key and not self.enable_offline_mode:
            raise ValueError(
                "GOOGLE_API_KEY not set in environment and offline mode is disabled"
            )
        return True

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_requests_per_minute": self.max_requests_per_minute,
        }


config = Config()
