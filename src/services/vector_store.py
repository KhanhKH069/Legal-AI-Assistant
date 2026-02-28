"""Vector Store Service"""
from datetime import datetime


class VectorStore:
    def __init__(self):
        self.documents = {}
    
    def add_document(self, doc_id: str, content: str, metadata: dict):
        self.documents[doc_id] = {
            'content': content,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
    
    def search(self, query: str, top_k: int = 3) -> list:
        results = []
        query_lower = query.lower()
        for doc_id, doc in self.documents.items():
            if any(word in doc['content'].lower() for word in query_lower.split()):
                results.append({
                    'id': doc_id,
                    'content': doc['content'],
                    'metadata': doc['metadata']
                })
        return results[:top_k]
