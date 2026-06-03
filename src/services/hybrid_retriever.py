import json
import pickle
from typing import Any, Dict, List, Optional
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.services.vector_db import get_vector_db
import re

def _tokenize(text: str) -> List[str]:
    return re.findall('\\w+', text.lower())
print('[HybridRetriever] Using fast regex tokenizer')
_reranker = None
_reranker_loaded = False

def _get_reranker():
    global _reranker, _reranker_loaded
    if _reranker_loaded:
        return _reranker
    try:
        from sentence_transformers import CrossEncoder
        print('[HybridRetriever] Loading huynhdat543/VietNamese_law_rerank...')
        _reranker = CrossEncoder('huynhdat543/VietNamese_law_rerank')
        print('[HybridRetriever] Reranker loaded')
    except Exception as e:
        print(f'[HybridRetriever] Reranker not available ({e}) – skipping rerank step')
        _reranker = None
    _reranker_loaded = True
    return _reranker

class HybridRetriever:

    def __init__(self, collection_name: str, persist_directory: str='./chroma_db', use_reranker: bool=True):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.vdb = get_vector_db(str(self.persist_directory))
        self.use_reranker = use_reranker
        self.bm25_index_path = self.persist_directory / f'bm25_index_{collection_name}.pkl'
        self.bm25_corpus_path = self.persist_directory / f'bm25_corpus_{collection_name}.json'
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_data: List[Dict] = []
        self.load_bm25()

    def load_bm25(self):
        if self.bm25_index_path.exists() and self.bm25_corpus_path.exists():
            try:
                with open(self.bm25_index_path, 'rb') as f:
                    self.bm25 = pickle.load(f)
                with open(self.bm25_corpus_path, 'r', encoding='utf-8') as f:
                    self.corpus_data = json.load(f)
                return
            except Exception as e:
                import logging
                logging.warning(f'[HybridRetriever] Error loading BM25 index: {e} – skipping')
        else:
            import logging
            logging.warning('[HybridRetriever] BM25 index not found. Keyword search will be disabled until index is built offline.')

    def build_bm25(self):
        data = self.vdb.get_all_documents(self.collection_name)
        if not data or not data.get('documents'):
            print('[HybridRetriever] No documents found in VectorDB to build BM25')
            return
        docs = data['documents']
        metadatas = data['metadatas']
        ids = data['ids']
        tokenized_corpus = [_tokenize(doc) for doc in docs]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.corpus_data = [{'id': ids[i], 'document': docs[i], 'metadata': metadatas[i]} for i in range(len(docs))]
            try:
                with open(self.bm25_index_path, 'wb') as f:
                    pickle.dump(self.bm25, f)
                with open(self.bm25_corpus_path, 'w', encoding='utf-8') as f:
                    json.dump(self.corpus_data, f, ensure_ascii=False)
                print(f'[HybridRetriever] BM25 index built with {len(docs)} docs')
            except Exception as e:
                print(f'[HybridRetriever] Error saving BM25 index: {e}')

    def retrieve(self, query: str, top_k: int=5) -> List[Dict[str, Any]]:
        results_map: Dict[str, Dict] = {}
        vector_results = self.vdb.query(self.collection_name, query, n_results=top_k * 3)
        if vector_results and vector_results.get('documents') and (len(vector_results['documents']) > 0):
            docs = vector_results['documents'][0]
            metas = vector_results['metadatas'][0]
            for rank, (doc, meta) in enumerate(zip(docs, metas)):
                if doc not in results_map:
                    results_map[doc] = {'metadata': meta, 'vector_rank': rank + 1, 'bm25_rank': 0}
                else:
                    results_map[doc]['vector_rank'] = rank + 1
        if self.bm25 and self.corpus_data:
            tokenized_query = _tokenize(query)
            bm25_scores = self.bm25.get_scores(tokenized_query)
            top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k * 3]
            for rank, idx in enumerate(top_indices):
                if bm25_scores[idx] > 0:
                    doc_content = self.corpus_data[idx]['document']
                    if doc_content not in results_map:
                        results_map[doc_content] = {'metadata': self.corpus_data[idx]['metadata'], 'vector_rank': 0, 'bm25_rank': rank + 1}
                    else:
                        results_map[doc_content]['bm25_rank'] = rank + 1
        k = 60
        fused: List[Dict[str, Any]] = []
        for doc, info in results_map.items():
            v_score = 1.0 / (k + info['vector_rank']) if info['vector_rank'] > 0 else 0.0
            b_score = 1.0 / (k + info['bm25_rank']) if info['bm25_rank'] > 0 else 0.0
            fused.append({'content': doc, 'metadata': info['metadata'], 'score': v_score + b_score})
        fused.sort(key=lambda x: x['score'], reverse=True)
        candidates = fused[:top_k * 2]
        if self.use_reranker and len(candidates) > 1:
            reranker = _get_reranker()
            if reranker is not None:
                try:
                    pairs = [[query, c['content']] for c in candidates]
                    scores = reranker.predict(pairs)
                    for i, c in enumerate(candidates):
                        c['reranker_score'] = float(scores[i])
                        c['score'] = float(scores[i])
                    candidates.sort(key=lambda x: x['score'], reverse=True)
                except Exception as e:
                    print(f'[HybridRetriever] Reranker prediction failed: {e}')
        return candidates[:top_k]
_hybrid_retrievers: Dict[str, HybridRetriever] = {}

def get_hybrid_retriever(collection_name: str) -> HybridRetriever:
    global _hybrid_retrievers
    if collection_name not in _hybrid_retrievers:
        _hybrid_retrievers[collection_name] = HybridRetriever(collection_name=collection_name)
    return _hybrid_retrievers[collection_name]