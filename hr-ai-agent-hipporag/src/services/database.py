"""SQL Database Service"""
from datetime import datetime


class SQLDatabase:
    def __init__(self):
        self.tables = {
            'employees': [],
            'policies': [],
            'audit_logs': []
        }
    
    def insert(self, table: str, data: dict):
        if table in self.tables:
            data['id'] = len(self.tables[table]) + 1
            data['created_at'] = datetime.now().isoformat()
            self.tables[table].append(data)
            return data['id']
        return None
    
    def query(self, table: str, filters: dict = None) -> list:
        if table not in self.tables:
            return []
        results = self.tables[table]
        if filters:
            results = [r for r in results if all(r.get(k) == v for k, v in filters.items())]
        return results
