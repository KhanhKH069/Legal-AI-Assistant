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

        from src.core.config import config

        # Initialize ChromaDB client
        if config.chromadb_host and config.chromadb_host != "localhost":
            self.client = chromadb.HttpClient(
                host=config.chromadb_host,
                port=config.chromadb_port,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
        else:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

        self.embedding_function = None
        from src.core.config import config

        if config.google_api_key and not config.enable_offline_mode:
            try:
                from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                class GoogleEmbedding(EmbeddingFunction):
                    def __init__(self, api_key: str):
                        self.emb = GoogleGenerativeAIEmbeddings(
                            model="models/gemini-embedding-2", google_api_key=api_key
                        )

                    def __call__(self, input: Documents) -> Embeddings:
                        embeddings = []
                        for text in input:
                            res = self.emb.embed_query(text)
                            embeddings.append(res)
                        return embeddings

                self.embedding_function = GoogleEmbedding(config.google_api_key)
            except Exception as e:
                print(f"Failed to init Google Embeddings: {e}")
        else:
            try:
                from chromadb.utils import embedding_functions

                # Try best multilingual model first, fall back to smaller model
                try:
                    self.embedding_function = (
                        embedding_functions.SentenceTransformerEmbeddingFunction(
                            model_name="truro7/vn-law-embedding"
                        )
                    )
                    print("[VectorDB] Using truro7/vn-law-embedding model")
                except Exception:
                    self.embedding_function = (
                        embedding_functions.SentenceTransformerEmbeddingFunction(
                            model_name="dangvantuan/vietnamese-document-embedding"
                        )
                    )
                    print("[VectorDB] Using dangvantuan/vietnamese-document-embedding model (fallback)")
            except Exception as e:
                print(f"Failed to init Multilingual Embeddings: {e}")

    def create_collection(self, collection_name: str, reset: bool = False):
        """Create or get a collection"""
        if reset:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass

        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_function,
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ):
        """Add documents to collection"""
        collection = self.create_collection(collection_name)

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        collection.add(documents=documents, metadatas=metadatas, ids=ids)

        return len(documents)

    def query(self, collection_name: str, query_text: str, n_results: int = 3) -> Dict:
        """Query the collection"""
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )

            results = collection.query(query_texts=[query_text], n_results=n_results)

            return results

        except Exception as e:
            print(f"Query error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_all_documents(self, collection_name: str) -> Dict:
        """Get all documents from collection for BM25 indexing"""
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )
            return collection.get()
        except Exception as e:
            print(f"Error getting documents: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def get_collection_count(self, collection_name: str) -> int:
        """Get number of documents in collection"""
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )
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
        "Lương: Trả vào ngày 10 hàng tháng",
    ]

    metadatas = [
        {
            "question": "Nghỉ phép bao nhiêu ngày?",
            "answer": "12 ngày/năm",
            "source": "hr_policy.txt",
        },
        {
            "question": "Giờ làm việc?",
            "answer": "8:30 - 17:30",
            "source": "hr_policy.txt",
        },
        {
            "question": "Khi nào trả lương?",
            "answer": "Ngày 10 hàng tháng",
            "source": "hr_policy.txt",
        },
    ]

    count = vdb.add_documents(collection_name, documents, metadatas)
    print(f"Added {count} documents")

    # Query
    results = vdb.query(collection_name, "Nghỉ phép mấy ngày?", n_results=1)

    if results["documents"][0]:
        print("\nQuery: Nghỉ phép mấy ngày?")
        print(f"Answer: {results['metadatas'][0][0]['answer']}")
        print(f"Distance: {results['distances'][0][0]}")
