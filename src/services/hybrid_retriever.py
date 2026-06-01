"""
Hybrid Retriever Service
Combines Vector Search (ChromaDB) and Keyword Search (BM25) using RRF Fusion,
then optionally re-ranks results with a cross-encoder model.

Improvements over v1:
- Vietnamese-aware BM25 tokenization via underthesea (falls back to whitespace split)
- Cross-encoder reranker (bge-reranker-v2-m3) applied after RRF for better precision
"""

import json
import pickle
from typing import Any, Dict, List, Optional
from pathlib import Path

from rank_bm25 import BM25Okapi
from src.services.vector_db import get_vector_db

# ---------------------------------------------------------------------------
# Vietnamese tokenizer (optional – falls back gracefully)
# ---------------------------------------------------------------------------
try:
    from underthesea import word_tokenize as _vn_tokenize

    def _tokenize(text: str) -> List[str]:
        return _vn_tokenize(text.lower(), format="text").split()

    print("[HybridRetriever] Using underthesea Vietnamese tokenizer")

except ImportError:

    def _tokenize(text: str) -> List[str]:  # type: ignore[misc]
        return text.lower().split()

    print("[HybridRetriever] underthesea not installed – using whitespace tokenizer")


# ---------------------------------------------------------------------------
# Cross-encoder reranker (BAAI/bge-reranker-v2-m3)
# ---------------------------------------------------------------------------
_reranker = None
_reranker_loaded = False


def _get_reranker():
    """Lazy-load the BGE reranker model (singleton)."""
    global _reranker, _reranker_loaded
    if _reranker_loaded:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder

        print("[HybridRetriever] Loading BAAI/bge-reranker-v2-m3...")
        _reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
        print("[HybridRetriever] Reranker loaded")
    except Exception as e:
        print(f"[HybridRetriever] Reranker not available ({e}) – skipping rerank step")
        _reranker = None
    _reranker_loaded = True
    return _reranker


class HybridRetriever:
    """Retriever that combines ChromaDB semantic search with BM25 exact match,
    then applies cross-encoder reranking for best precision."""

    def __init__(
        self,
        collection_name: str,
        persist_directory: str = "./chroma_db",
        use_reranker: bool = True,
    ):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.vdb = get_vector_db(str(self.persist_directory))
        self.use_reranker = use_reranker

        # BM25 index paths (separated by collection)
        self.bm25_index_path = self.persist_directory / f"bm25_index_{collection_name}.pkl"
        self.bm25_corpus_path = self.persist_directory / f"bm25_corpus_{collection_name}.json"

        self.bm25: Optional[BM25Okapi] = None
        self.corpus_data: List[Dict] = []

        self.load_bm25()

    def load_bm25(self):
        """Load BM25 index from disk, rebuild if missing or corrupted."""
        if self.bm25_index_path.exists() and self.bm25_corpus_path.exists():
            try:
                with open(self.bm25_index_path, "rb") as f:
                    self.bm25 = pickle.load(f)
                with open(self.bm25_corpus_path, "r", encoding="utf-8") as f:
                    self.corpus_data = json.load(f)
                return
            except Exception as e:
                print(f"[HybridRetriever] Error loading BM25 index: {e} – rebuilding")
        self.build_bm25()

    def build_bm25(self):
        """Build BM25 index from current ChromaDB data using Vietnamese tokenizer."""
        data = self.vdb.get_all_documents(self.collection_name)
        if not data or not data.get("documents"):
            print("[HybridRetriever] No documents found in VectorDB to build BM25")
            return

        docs = data["documents"]
        metadatas = data["metadatas"]
        ids = data["ids"]

        # Vietnamese-aware tokenization
        tokenized_corpus = [_tokenize(doc) for doc in docs]

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.corpus_data = [
                {"id": ids[i], "document": docs[i], "metadata": metadatas[i]}
                for i in range(len(docs))
            ]
            # Persist to disk
            try:
                with open(self.bm25_index_path, "wb") as f:
                    pickle.dump(self.bm25, f)
                with open(self.bm25_corpus_path, "w", encoding="utf-8") as f:
                    json.dump(self.corpus_data, f, ensure_ascii=False)
                print(f"[HybridRetriever] BM25 index built with {len(docs)} docs")
            except Exception as e:
                print(f"[HybridRetriever] Error saving BM25 index: {e}")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve documents using Hybrid Search (RRF) + optional cross-encoder reranking."""
        results_map: Dict[str, Dict] = {}

        # 1. Vector Search
        vector_results = self.vdb.query(
            self.collection_name, query, n_results=top_k * 3
        )
        if (
            vector_results
            and vector_results.get("documents")
            and len(vector_results["documents"]) > 0
        ):
            docs = vector_results["documents"][0]
            metas = vector_results["metadatas"][0]
            for rank, (doc, meta) in enumerate(zip(docs, metas)):
                if doc not in results_map:
                    results_map[doc] = {
                        "metadata": meta,
                        "vector_rank": rank + 1,
                        "bm25_rank": 0,
                    }
                else:
                    results_map[doc]["vector_rank"] = rank + 1

        # 2. BM25 Search (Vietnamese tokenizer)
        if self.bm25 and self.corpus_data:
            tokenized_query = _tokenize(query)
            bm25_scores = self.bm25.get_scores(tokenized_query)
            top_indices = sorted(
                range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
            )[: top_k * 3]
            for rank, idx in enumerate(top_indices):
                if bm25_scores[idx] > 0:
                    doc_content = self.corpus_data[idx]["document"]
                    if doc_content not in results_map:
                        results_map[doc_content] = {
                            "metadata": self.corpus_data[idx]["metadata"],
                            "vector_rank": 0,
                            "bm25_rank": rank + 1,
                        }
                    else:
                        results_map[doc_content]["bm25_rank"] = rank + 1

        # 3. Reciprocal Rank Fusion (RRF k=60)
        k = 60
        fused: List[Dict[str, Any]] = []
        for doc, info in results_map.items():
            v_score = (
                1.0 / (k + info["vector_rank"]) if info["vector_rank"] > 0 else 0.0
            )
            b_score = 1.0 / (k + info["bm25_rank"]) if info["bm25_rank"] > 0 else 0.0
            fused.append(
                {
                    "content": doc,
                    "metadata": info["metadata"],
                    "score": v_score + b_score,
                }
            )
        fused.sort(key=lambda x: x["score"], reverse=True)
        candidates = fused[: top_k * 2]  # Keep more for reranker

        # 4. Cross-encoder Reranking (optional)
        if self.use_reranker and len(candidates) > 1:
            reranker = _get_reranker()
            if reranker is not None:
                try:
                    # Format for SentenceTransformer CrossEncoder: list of (query, document) pairs
                    pairs = [[query, c["content"]] for c in candidates]
                    scores = reranker.predict(pairs)

                    for i, c in enumerate(candidates):
                        c["reranker_score"] = float(scores[i])
                        c["score"] = float(scores[i]) # override score with reranker score

                    candidates.sort(key=lambda x: x["score"], reverse=True)
                except Exception as e:
                    print(f"[HybridRetriever] Reranker prediction failed: {e}")

        return candidates[:top_k]


# ---------------------------------------------------------------------------
# Singleton Pattern
# ---------------------------------------------------------------------------
_hybrid_retrievers: Dict[str, HybridRetriever] = {}


def get_hybrid_retriever(collection_name: str) -> HybridRetriever:
    """Get singleton HybridRetriever instance per collection."""
    global _hybrid_retrievers
    if collection_name not in _hybrid_retrievers:
        _hybrid_retrievers[collection_name] = HybridRetriever(collection_name=collection_name)
    return _hybrid_retrievers[collection_name]
