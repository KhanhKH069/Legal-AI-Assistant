#!/usr/bin/env python3
"""
scripts/reindex.py — Reindex HR Knowledge Base into ChromaDB.

Run this script whenever you add or update documents in the documents/ folder
to keep the RAG vector store in sync.

Usage:
    python scripts/reindex.py                  # reindex all documents
    python scripts/reindex.py --reset          # wipe collection and rebuild
    python scripts/reindex.py --dry-run        # preview without writing

The script reads Markdown files from documents/, splits them into Q&A chunks,
and upserts them into ChromaDB collection 'hr_policies'.
"""

import argparse
import re
import sys
from pathlib import Path

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ChromaDB uses Pydantic v1 internally which is incompatible with Python 3.14+.
# On affected environments, the script will still parse documents and print stats
# (--dry-run mode), but cannot write to ChromaDB.
_CHROMA_AVAILABLE = True
try:
    from src.services.vector_db import get_vector_db  # noqa: E402
except Exception as _e:
    _CHROMA_AVAILABLE = False
    print(
        f"[reindex] WARNING: ChromaDB unavailable ({_e.__class__.__name__}: {_e})\n"
        "  Dry-run mode will still work. To write to ChromaDB, use Python 3.10–3.12."
    )

COLLECTION_NAME = "hr_policies"
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"

# Markdown files to index (relative to documents/)
# Add new policy files here as needed
TARGET_FILES = [
    "01_HR_Policies.md",
    "02_Leave_Policies.md",
    "03_Compensation.md",
    "04_Onboarding.md",
    "05_Benefits.md",
    "06_Compliance.md",
    "attendance_policy.md",
    "benefits_policy.md",
    "esignature_guide.md",
    "helpdesk_guide.md",
    "recruitment_process.md",
]


def _parse_qa_chunks(filepath: Path) -> list[dict]:
    """Extract Q&A pairs from a Markdown document.

    Supports two formats:
    1. ``**Câu hỏi:**`` / ``**Trả lời:**`` structured pairs (HR Policies format)
    2. ``## Heading`` sections treated as standalone knowledge chunks
    """
    text = filepath.read_text(encoding="utf-8")
    chunks: list[dict] = []

    # --- Format 1: structured Q&A pairs ---
    entries = re.split(r"\n---+\n", text)
    for entry in entries:
        lines = entry.strip().splitlines()
        qline, ans_lines = None, []
        for line in lines:
            if line.startswith("**Câu hỏi:**"):
                qline = line.replace("**Câu hỏi:**", "").strip()
                ans_lines = []
            elif qline is not None:
                if line.startswith("**Biến thể:"):
                    continue
                if line.startswith("**Trả lời:"):
                    ans_lines.append(line.replace("**Trả lời:", "").strip())
                else:
                    ans_lines.append(line)
        if qline and ans_lines:
            answer = "\n".join(ans_lines).strip()
            chunks.append(
                {
                    "question": qline,
                    "answer": answer,
                    "source_file": filepath.name,
                    "chunk_type": "qa_pair",
                }
            )

    # --- Format 2: heading-based sections (fallback) ---
    if not chunks:
        sections = re.split(r"\n(?=## )", text)
        for section in sections:
            heading_match = re.match(r"## (.+)", section)
            if not heading_match:
                continue
            heading = heading_match.group(1).strip()
            body = section[heading_match.end() :].strip()
            if body:
                chunks.append(
                    {
                        "question": heading,
                        "answer": body,
                        "source_file": filepath.name,
                        "chunk_type": "section",
                    }
                )

    return chunks


def reindex(reset: bool = False, dry_run: bool = False) -> None:
    """Run the full reindex pipeline."""
    if not _CHROMA_AVAILABLE and not dry_run:
        print(
            "[reindex] ❌ Cannot write to ChromaDB — library unavailable.\n"
            "   Run with --dry-run to preview document parsing, or switch to Python 3.10–3.12."
        )
        return

    all_documents: list[str] = []
    all_metadatas: list[dict] = []
    all_ids: list[str] = []

    total_files = 0
    missing_files = []

    for filename in TARGET_FILES:
        filepath = DOCUMENTS_DIR / filename
        if not filepath.exists():
            missing_files.append(filename)
            continue

        total_files += 1
        chunks = _parse_qa_chunks(filepath)
        print(f"  [{filepath.name}] -> {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            doc_id = f"{filepath.stem}_{i:04d}"
            document_text = f"{chunk['question']}\n{chunk['answer']}"
            all_documents.append(document_text)
            all_metadatas.append(chunk)
            all_ids.append(doc_id)

    print(
        f"\n[reindex] Summary: {total_files} files, {len(all_documents)} total chunks"
    )

    if missing_files:
        print(f"[reindex] WARNING — missing files: {', '.join(missing_files)}")

    if dry_run:
        print("[reindex] DRY RUN — no data written to ChromaDB.")
        return

    vdb = get_vector_db()
    if reset:
        print(f"[reindex] Resetting collection '{COLLECTION_NAME}'…")
        vdb.create_collection(COLLECTION_NAME, reset=True)
    else:
        vdb.create_collection(COLLECTION_NAME, reset=False)

    if all_documents:
        vdb.add_documents(
            collection_name=COLLECTION_NAME,
            documents=all_documents,
            metadatas=all_metadatas,
            ids=all_ids,
        )
        final_count = vdb.get_collection_count(COLLECTION_NAME)
        print(f"[reindex] ✅ Done — {final_count} documents now in '{COLLECTION_NAME}'.")
    else:
        print("[reindex] ⚠️  No chunks found — collection unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reindex HR knowledge base into ChromaDB"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the collection from scratch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse documents and print stats without writing to ChromaDB",
    )
    args = parser.parse_args()
    reindex(reset=args.reset, dry_run=args.dry_run)
