import os
from dotenv import load_dotenv
load_dotenv(override=True)

class Config:

    def __init__(self):
        self.llm_api_key = os.getenv('OPENAI_API_KEY', 'ollama')
        self.llm_api_base = os.getenv('OPENAI_API_BASE', 'http://localhost:11434/v1')
        self.llm_model_name = os.getenv('LLM_MODEL_NAME', 'qwen2.5:7b')
        self.enable_analytics = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
        self.enable_audit_log = os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true'
        self.enable_offline_mode = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
        if self.enable_offline_mode:
            print('[CONFIG] Offline mode enabled – LLM calls will be skipped in tests')
        else:
            print(f'[CONFIG] using Local LLM model: {self.llm_model_name} at {self.llm_api_base}')
        self.temperature = float(os.getenv('TEMPERATURE', '0.0'))
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4000'))
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '10'))
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///data/sql_db/legal_agent.db')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.chromadb_host = os.getenv('CHROMADB_HOST', 'localhost')
        self.chromadb_port = int(os.getenv('CHROMADB_PORT', '8000'))
        self.chromadb_dir = os.getenv('CHROMADB_DIR', './chroma_db')
        self.statutory_collection = os.getenv('STATUTORY_COLLECTION', 'legal_statutory')
        self.caselaw_collection = os.getenv('CASELAW_COLLECTION', 'legal_caselaw')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'data/logs/app.log')

    def validate(self) -> bool:
        if not self.llm_api_base and (not self.enable_offline_mode):
            raise ValueError('OPENAI_API_BASE not set in environment and offline mode is disabled')
        return True

    def to_dict(self):
        return {'model_name': self.llm_model_name, 'temperature': self.temperature, 'max_tokens': self.max_tokens, 'max_requests_per_minute': self.max_requests_per_minute}
config = Config()