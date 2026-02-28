"""Memory Manager Service"""

class MemoryManager:
    def __init__(self):
        self.conversations = {}
    
    def add_message(self, user_id: str, message: dict):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        self.conversations[user_id].append(message)
    
    def get_history(self, user_id: str, limit: int = 10):
        return self.conversations.get(user_id, [])[-limit:]
    
    def clear(self, user_id: str):
        if user_id in self.conversations:
            self.conversations[user_id] = []
