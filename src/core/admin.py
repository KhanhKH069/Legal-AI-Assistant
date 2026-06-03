import logging
from typing import Any, Dict, List
logger = logging.getLogger(__name__)

class AdminPanel:

    def __init__(self, db):
        self.db = db
        self.config = {'enable_analytics': True, 'enable_audit_log': True, 'max_response_length': 2000}

    def get_config(self, key: str=None):
        if key:
            return self.config.get(key)
        return self.config

    def update_config(self, key: str, value: Any):
        self.config[key] = value
        logger.info(f'Config updated: {key} = {value}')

    def get_audit_logs(self, user_id: str=None, limit: int=100) -> List[Dict]:
        logs = self.db.query('audit_logs')
        if user_id:
            logs = [log for log in logs if log['user_id'] == user_id]
        return logs[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        logs = self.db.query('audit_logs')
        stats = {'total_requests': len(logs), 'requests_by_action': {}, 'requests_by_user': {}}
        for log in logs:
            action = log['action']
            user_id = log['user_id']
            stats['requests_by_action'][action] = stats['requests_by_action'].get(action, 0) + 1
            stats['requests_by_user'][user_id] = stats['requests_by_user'].get(user_id, 0) + 1
        return stats