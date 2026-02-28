"""
Vector Database Service - LangChain v1.x Compatible
Simple ChromaDB wrapper for HR knowledge base
"""

from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings


class VectorDB:
    """Simple ChromaDB wrapper for vector storage and retrieval"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client"""
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
    
    def create_collection(self, collection_name: str, reset: bool = False):
        """Create or get a collection"""
        if reset:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass
        
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None
    ):
        """Add documents to collection"""
        collection = self.create_collection(collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return len(documents)
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 3
    ) -> Dict:
        """Query the collection"""
        try:
            collection = self.client.get_collection(collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            print(f"Query error: {e}")
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get number of documents in collection"""
        try:
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except Exception:
            return 0
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        collections = self.client.list_collections()
        return [c.name for c in collections]
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False


# Singleton instance
_vector_db_instance = None

def get_vector_db(persist_directory: str = "./chroma_db") -> VectorDB:
    """Get singleton VectorDB instance"""
    global _vector_db_instance
    
    if _vector_db_instance is None:
        _vector_db_instance = VectorDB(persist_directory)
    
    return _vector_db_instance


# Example usage
if __name__ == "__main__":
    # Initialize
    vdb = get_vector_db()
    
    # Create collection
    collection_name = "test_collection"
    
    # Add documents
    documents = [
        "Chính sách nghỉ phép: 12 ngày/năm",
        "Thời gian làm việc: 8:30 - 17:30",
        "Lương: Trả vào ngày 10 hàng tháng"
    ]
    
    metadatas = [
        {"question": "Nghỉ phép bao nhiêu ngày?", "answer": "12 ngày/năm", "source": "hr_policy.txt"},
        {"question": "Giờ làm việc?", "answer": "8:30 - 17:30", "source": "hr_policy.txt"},
        {"question": "Khi nào trả lương?", "answer": "Ngày 10 hàng tháng", "source": "hr_policy.txt"}
    ]
    
    count = vdb.add_documents(collection_name, documents, metadatas)
    print(f"Added {count} documents")
    
    # Query
    results = vdb.query(collection_name, "Nghỉ phép mấy ngày?", n_results=1)
    
    if results['documents'][0]:
        print("\nQuery: Nghỉ phép mấy ngày?")
        print(f"Answer: {results['metadatas'][0][0]['answer']}")
        print(f"Distance: {results['distances'][0][0]}")