"""
API Gateway - Authentication & Rate Limiting
"""

import logging
import time

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
