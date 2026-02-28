"""Audit Logger Service"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, db):
        self.db = db
    
    def log(self, user_id: str, action: str, details: dict):
        log_entry = {
            'user_id': user_id,
            'action': action,
            'details': json.dumps(details),
            'timestamp': datetime.now().isoformat()
        }
        self.db.insert('audit_logs', log_entry)
        logger.info(f"Audit: {user_id} - {action}")
