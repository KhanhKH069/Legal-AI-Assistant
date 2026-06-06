import logging
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class VectorDB:

    def __init__(self, persist_directory: str = './chroma_db'):
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        from src.core.config import config
        if config.chromadb_host and config.chromadb_host != 'localhost':
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
        try:
            from chromadb.utils import embedding_functions
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name='truro7/vn-law-embedding'
            )
            logger.info('[VectorDB] Using truro7/vn-law-embedding model')
        except Exception as e:
            logger.error('[VectorDB] Error loading embedding model: %s', e)

    def create_collection(self, collection_name: str, reset: bool = False):
        if reset:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={'hnsw:space': 'cosine'},
            embedding_function=self.embedding_function,
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ):
        collection = self.create_collection(collection_name)
        if ids is None:
            ids = [f'doc_{i}' for i in range(len(documents))]
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return len(documents)

    def query(self, collection_name: str, query_text: str, n_results: int = 3) -> Dict:
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )
            results = collection.query(query_texts=[query_text], n_results=n_results)
            return results
        except Exception as e:
            logger.error('[VectorDB] Query error for collection "%s": %s', collection_name, e)
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}

    def get_all_documents(self, collection_name: str) -> Dict:
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )
            return collection.get()
        except Exception as e:
            logger.error('[VectorDB] Error getting documents from "%s": %s', collection_name, e)
            return {'ids': [], 'documents': [], 'metadatas': []}

    def get_collection_count(self, collection_name: str) -> int:
        try:
            collection = self.client.get_collection(
                collection_name, embedding_function=self.embedding_function
            )
            return collection.count()
        except Exception:
            return 0

    def list_collections(self) -> List[str]:
        collections = self.client.list_collections()
        return [c.name for c in collections]

    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception:
            return False


_vector_db_instance = None


def get_vector_db(persist_directory: str = './chroma_db') -> VectorDB:
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDB(persist_directory)
    return _vector_db_instance