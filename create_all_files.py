#!/usr/bin/env python3
"""
Script to create all HR AI Agent project files
"""

from pathlib import Path

BASE_DIR = Path(".")

# File contents dictionary
files = {
    # ============= SRC FILES =============
    "src/__init__.py": '"""HR AI Agent - Main Package"""',
    
    "src/core/__init__.py": '"""Core components"""',
    
    "src/core/config.py": '''"""
Configuration Management
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model_name = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        self.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10"))
        
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_requests_per_minute": self.max_requests_per_minute,
        }

config = Config()
''',

    "src/core/gateway.py": '''"""
API Gateway - Authentication & Rate Limiting
"""

import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class APIGateway:
    """API Gateway with authentication and rate limiting"""
    
    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        self.rate_limits = {}
        self.max_requests_per_minute = 10
        self.authenticated_users = {
            'user001': {'role': 'employee', 'name': 'Nguyễn Văn A'},
            'user002': {'role': 'hr', 'name': 'HR Manager'},
            'admin': {'role': 'admin', 'name': 'Admin'},
        }
    
    def authenticate(self, user_id: str, api_key: str = None) -> bool:
        """Authenticate user"""
        return user_id in self.authenticated_users
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit"""
        now = time.time()
        
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        self.rate_limits[user_id] = [
            ts for ts in self.rate_limits[user_id]
            if now - ts < 60
        ]
        
        if len(self.rate_limits[user_id]) >= self.max_requests_per_minute:
            return False
        
        self.rate_limits[user_id].append(now)
        return True
    
    def process_request(self, user_id: str, message: str, api_key: str = None) -> dict:
        """Process incoming request"""
        
        if not self.authenticate(user_id, api_key):
            return {
                'status': 'error',
                'message': 'Authentication failed',
                'code': 401
            }
        
        if not self.check_rate_limit(user_id):
            return {
                'status': 'error',
                'message': 'Rate limit exceeded',
                'code': 429
            }
        
        self.audit_logger.log(user_id, 'api_request', {'message': message})
        
        return {
            'status': 'success',
            'user_id': user_id,
            'user_info': self.authenticated_users[user_id],
            'message': message
        }
''',

    "src/core/admin.py": '''"""
Admin Panel - Configuration & Monitoring
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AdminPanel:
    """Admin panel for system management"""
    
    def __init__(self, db):
        self.db = db
        self.config = {
            'enable_analytics': True,
            'enable_audit_log': True,
            'max_response_length': 2000,
        }
    
    def get_config(self, key: str = None):
        """Get configuration"""
        if key:
            return self.config.get(key)
        return self.config
    
    def update_config(self, key: str, value: Any):
        """Update configuration"""
        self.config[key] = value
        logger.info(f"Config updated: {key} = {value}")
    
    def get_audit_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        logs = self.db.query('audit_logs')
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        return logs[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        logs = self.db.query('audit_logs')
        
        stats = {
            'total_requests': len(logs),
            'requests_by_action': {},
            'requests_by_user': {},
        }
        
        for log in logs:
            action = log['action']
            user_id = log['user_id']
            
            stats['requests_by_action'][action] = stats['requests_by_action'].get(action, 0) + 1
            stats['requests_by_user'][user_id] = stats['requests_by_user'].get(user_id, 0) + 1
        
        return stats
''',
}

print("Creating all files...")
total = 0

for filepath, content in files.items():
    full_path = BASE_DIR / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)
    total += 1
    print(f" Created {filepath}")

print(f"\n Created {total} files successfully!")

