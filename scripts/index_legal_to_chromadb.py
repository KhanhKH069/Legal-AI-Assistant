#!/usr/bin/env python3
"""
Index Vietnamese Legal Datasets into ChromaDB

Collections created:
  - legal_statutory : Phap dien (Dieu luat) - for statutory law lookup
  - legal_caselaw   : An le & Ban an      - for case law lookup

Usage:
  python scripts/index_legal_to_chromadb.py [--max-statutory 5000] [--max-caselaw 2000] [--reset]
"""

import argparse
import sys
import os
from pathlib import Path
import hashlib

# Fix Windows terminal encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

RAW_DIR = Path("data/raw")
CHROMA_DIR = "./chroma_db"

# ─────────────────────────────────────────────────────────────────────────────
# Direct ChromaDB + SentenceTransformer setup (bypass src.core.config)
# This avoids load_dotenv(override=True) from disabling offline mode
# ─────────────────────────────────────────────────────────────────────────────

def _build_chroma_client():
    """Create a persistent ChromaDB client with local SentenceTransformer embeddings."""
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions

    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )

    # Try best multilingual model, fallback to smaller one
    try:
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-large"
        )
        print("[INDEX] Using embedding: multilingual-e5-large")
    except Exception:
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("[INDEX] Using embedding: MiniLM-L12-v2 (fallback)")

    return client, emb_fn


_client = None
_emb_fn = None


def _get_or_create_collection(name: str, reset: bool = False):
    global _client, _emb_fn
    if _client is None:
        _client, _emb_fn = _build_chroma_client()

    if reset:
        try:
            _client.delete_collection(name)
            print(f"  -> Xoa collection cu: {name}")
        except Exception:
            pass

    return _client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=_emb_fn,
    )


def _add_documents_direct(collection_name: str, documents, metadatas, ids, reset: bool = False):
    col = _get_or_create_collection(collection_name, reset=False)  # reset done separately
    col.add(documents=documents, metadatas=metadatas, ids=ids)
    return len(documents)



def _clean_text(text) -> str:
    """Sanitize text for ChromaDB (must be non-empty string)."""
    if text is None:
        return ""
    s = str(text).strip()
    return s if s else ""


def _make_id(prefix: str, row_idx: int, extra: str = "") -> str:
    """Create a stable, unique ChromaDB document ID."""
    raw = f"{prefix}_{row_idx}_{extra}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# 1. INDEX STATUTORY LAW (Pháp điển)
# ─────────────────────────────────────────────────────────────────────────────

def index_statutory(max_rows=None, reset: bool = False):
    """Index phapdien articles into ChromaDB collection 'legal_statutory'."""
    import pandas as pd

    parquet_path = RAW_DIR / "phapdien_articles.parquet"
    if not parquet_path.exists():
        print(f"[ERROR] {parquet_path} khong ton tai. Chay download_datasets.py truoc.")
        return 0

    print("\n[1/2] Indexing Phap dien -> collection: legal_statutory ...")
    df = pd.read_parquet(parquet_path)
    if max_rows:
        df = df.head(max_rows)
    print(f"  So dieu luat se index: {len(df):,}")

    # Create / reset collection via direct client
    col = _get_or_create_collection("legal_statutory", reset=reset)

    BATCH = 100  # Smaller batch = faster feedback & safer
    total_indexed = 0

    for start in range(0, len(df), BATCH):
        batch = df.iloc[start: start + BATCH]
        documents, metadatas, ids = [], [], []

        for idx, row in batch.iterrows():
            content_text = _clean_text(row.get("content_text"))
            article_title = _clean_text(row.get("article_title"))
            chapter_title = _clean_text(row.get("chapter_title"))
            subject_title = _clean_text(row.get("subject_title"))
            topic_title = _clean_text(row.get("topic_title"))
            source_note  = _clean_text(row.get("source_note_text"))
            source_url   = _clean_text(row.get("source_url"))

            if not content_text:
                continue  # skip empty articles

            # Build rich text blob for embedding
            text_blob = f"""Chủ đề: {topic_title}
Đề mục: {subject_title}
Chương: {chapter_title}
Điều: {article_title}
Nội dung:
{content_text}"""
            if source_note:
                text_blob += f"\nNguồn: {source_note}"

            # Truncate to avoid token limits
            text_blob = text_blob[:4000]

            meta = {
                "article_title":  article_title or "Không rõ",
                "chapter_title":  chapter_title or "",
                "subject_title":  subject_title or "",
                "topic_title":    topic_title or "",
                "source_url":     source_url or "",
                "source_note":    source_note[:500] if source_note else "",
                "data_type":      "statutory",
            }

            doc_id = _make_id("stat", int(idx), article_title)
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)

        if documents:
            try:
                col.add(documents=documents, metadatas=metadatas, ids=ids)
                total_indexed += len(documents)
            except Exception as e:
                print(f"  [WARN] Batch {start}-{start+BATCH}: {e}")

        pct = min(100, int((start + BATCH) / len(df) * 100))
        print(f"  Progress: {pct}% ({total_indexed:,} docs indexed)...", end="\r")

    print(f"\n  OK - Da index {total_indexed:,} dieu luat vao [legal_statutory]")
    return total_indexed


# ─────────────────────────────────────────────────────────────────────────────
# 2. INDEX CASE LAW (Án lệ)
# ─────────────────────────────────────────────────────────────────────────────

def index_caselaw(max_rows=None, reset: bool = False):
    """Index anle documents into ChromaDB collection 'legal_caselaw'."""
    import pandas as pd

    parquet_path = RAW_DIR / "anle_documents.parquet"
    if not parquet_path.exists():
        print(f"[ERROR] {parquet_path} khong ton tai. Chay download_datasets.py truoc.")
        return 0

    print("\n[2/2] Indexing An le -> collection: legal_caselaw ...")
    df = pd.read_parquet(parquet_path)
    if max_rows:
        df = df.head(max_rows)
    print(f"  So ban an se index: {len(df):,}")

    col = _get_or_create_collection("legal_caselaw", reset=reset)

    BATCH = 50  # Case law docs are longer
    total_indexed = 0

    for start in range(0, len(df), BATCH):
        batch = df.iloc[start: start + BATCH]
        documents, metadatas, ids = [], [], []

        for idx, row in batch.iterrows():
            doc_name         = _clean_text(row.get("doc_name"))
            title            = _clean_text(row.get("title"))
            subject          = _clean_text(row.get("subject"))
            case_type        = _clean_text(row.get("case_type"))
            doc_subtype      = _clean_text(row.get("doc_subtype"))
            year             = str(row.get("year", "")) if row.get("year") else ""
            markdown         = _clean_text(row.get("markdown"))
            principle_text   = _clean_text(row.get("principle_text"))
            issuing_authority = _clean_text(row.get("issuing_authority"))
            court_level      = _clean_text(row.get("court_level"))
            detail_url       = _clean_text(row.get("detail_url"))
            applied_article  = _clean_text(row.get("applied_article_code"))
            precedent_num    = _clean_text(row.get("precedent_number"))

            # Primary text: use principle_text first (most concise), fallback to markdown
            primary_text = principle_text if principle_text else markdown
            if not primary_text:
                continue

            # Build embedding text
            text_blob = f"""Tên bản án: {title or doc_name}
Loại vụ án: {case_type} - {doc_subtype}
Lĩnh vực: {subject}
Tòa án: {issuing_authority} ({court_level})
Năm: {year}
Điều luật áp dụng: {applied_article}
Nguyên tắc pháp lý:
{primary_text}"""
            if precedent_num:
                text_blob = f"Án lệ số: {precedent_num}\n" + text_blob

            # Truncate long docs
            text_blob = text_blob[:6000]

            meta = {
                "doc_name":        doc_name or title or "",
                "title":           title or "",
                "case_type":       case_type or "",
                "doc_subtype":     doc_subtype or "",
                "subject":         subject or "",
                "year":            year or "",
                "court_level":     court_level or "",
                "detail_url":      detail_url or "",
                "applied_article": applied_article or "",
                "precedent_number": precedent_num or "",
                "data_type":       "caselaw",
            }

            doc_id = _make_id("case", int(idx), doc_name)
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)

        if documents:
            try:
                col.add(documents=documents, metadatas=metadatas, ids=ids)
                total_indexed += len(documents)
            except Exception as e:
                print(f"  [WARN] Batch {start}-{start+BATCH}: {e}")

        pct = min(100, int((start + BATCH) / len(df) * 100))
        print(f"  Progress: {pct}% ({total_indexed:,} docs indexed)...", end="\r")

    print(f"\n  OK - Da index {total_indexed:,} ban an vao [legal_caselaw]")
    return total_indexed


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Index legal datasets into ChromaDB")
    parser.add_argument("--max-statutory", type=int, default=None)
    parser.add_argument("--max-caselaw",   type=int, default=None)
    parser.add_argument("--reset", action="store_true", help="Delete old collections before re-indexing")
    args = parser.parse_args()

    print("=" * 60)
    print("  LEGAL AI ASSISTANT - ChromaDB Indexer (Local Embeddings)")
    print("=" * 60)

    # Initialize the ChromaDB client + embeddings (local SentenceTransformer)
    _get_or_create_collection("legal_statutory", reset=False)  # triggers lazy init

    n1 = index_statutory(max_rows=args.max_statutory, reset=args.reset)
    n2 = index_caselaw(max_rows=args.max_caselaw, reset=args.reset)

    print("\n" + "=" * 60)
    print("  Indexing DONE")
    print(f"  legal_statutory : {n1:,} documents")
    print(f"  legal_caselaw   : {n2:,} documents")
    print("=" * 60)
    print("  Next: uvicorn api.main:app --reload")
    print("=" * 60)


if __name__ == "__main__":
    main()
