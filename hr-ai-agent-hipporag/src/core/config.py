"""Configuration Management - Gemini API"""
import os


class Config:
    """Application configuration for Gemini"""
    
    def __init__(self):
        # Gemini API Configuration
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.model_name = os.getenv("MODEL_NAME", "gemini-pro")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        
        # Gateway Configuration
        self.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
        
        # Database Configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///data/sql_db/hr_agent.db")
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "data/logs/app.log")
        
        # Feature Flags
        self.enable_analytics = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        self.enable_audit_log = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")
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
