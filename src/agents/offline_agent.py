"""Simple offline QA agent that uses local markdown files and Vector DB.

Improvements:
- Hash-based cache: only re-index when .md files actually change (no reset every startup)
- Vietnamese-aware tokenization via underthesea (with graceful fallback)
"""

import hashlib
import json
from pathlib import Path
import re
from typing import List
from src.services.vector_db import VectorDB

KB_DIR = Path("documents")
KB_FILES = sorted(KB_DIR.glob("*.md"))
CACHE_META_PATH = Path("./chroma_db_offline/kb_hash.json")

vdb = None
_db_initialized = False

# ---------------------------------------------------------------------------
# Vietnamese tokenizer (optional – falls back to whitespace split gracefully)
# ---------------------------------------------------------------------------
try:
    from underthesea import word_tokenize as _vn_tokenize

    def _tokenize(text: str) -> List[str]:
        return _vn_tokenize(text.lower(), format="text").split()

except ImportError:

    def _tokenize(text: str) -> List[str]:  # type: ignore[misc]
        return text.lower().split()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_kb_hash() -> str:
    """Return a SHA-256 hash of all KB markdown file contents combined."""
    h = hashlib.sha256()
    for path in KB_FILES:
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()


def _load_stored_hash() -> str:
    """Return previously stored hash or empty string if not found."""
    if CACHE_META_PATH.exists():
        try:
            meta = json.loads(CACHE_META_PATH.read_text(encoding="utf-8"))
            return meta.get("hash", "")
        except Exception:
            pass
    return ""


def _save_hash(hash_val: str) -> None:
    CACHE_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_META_PATH.write_text(json.dumps({"hash": hash_val}), encoding="utf-8")


# ---------------------------------------------------------------------------
# KB loading
# ---------------------------------------------------------------------------


def _load_kb(force: bool = False):
    global vdb, _db_initialized
    vdb = VectorDB(persist_directory="./chroma_db_offline")

    current_hash = _compute_kb_hash()
    stored_hash = _load_stored_hash()

    if not force and current_hash == stored_hash:
        # Files unchanged – reuse existing ChromaDB collection as-is
        print("[OFFLINE_AGENT] KB unchanged – using cached index (fast startup)")
        _db_initialized = True
        return

    print("[OFFLINE_AGENT] KB changed or first run – rebuilding index…")
    vdb.create_collection("offline_hr_kb", reset=True)

    qa_docs: List[str] = []
    qa_metadatas: List[dict] = []

    for path in KB_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        entries = re.split(r"\n---+\n", text)
        for entry in entries:
            lines = entry.strip().splitlines()
            if not lines:
                continue
            qline = None
            ans_lines: List[str] = []
            in_variants = False
            for line in lines:
                if line.startswith("### Q"):
                    continue
                if line.startswith("**Câu hỏi:**"):
                    qline = line.replace("**Câu hỏi:**", "").strip()
                    in_variants = False
                elif qline is not None:
                    if line.startswith("**Biến thể:**"):
                        in_variants = True
                        continue
                    if line.startswith("**Trả lời:**"):
                        in_variants = False
                        ans_lines.append(line.replace("**Trả lời:**", "").strip())
                        continue
                    if in_variants:
                        continue
                    ans_lines.append(line)
            if qline and ans_lines:
                answer = "\n".join(ans_lines).strip()
                qa_docs.append(qline)
                qa_metadatas.append({"answer": answer, "file": path.name})

    if qa_docs:
        vdb.add_documents(
            collection_name="offline_hr_kb",
            documents=qa_docs,
            metadatas=qa_metadatas,
        )
        print(f"[OFFLINE_AGENT] Indexed {len(qa_docs)} QA pairs into ChromaDB")

    # Persist hash so next startup skips rebuild
    _save_hash(current_hash)
    _db_initialized = True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def answer_question(question: str) -> str:
    """Return the best matching answer from the loaded knowledge base."""
    global vdb, _db_initialized
    if not _db_initialized:
        _load_kb()

    q_lower = question.lower()

    # Handle auto-generated CV upload prompt in offline mode
    import re

    cv_match = re.search(r"tải lên file cv:\s*(.*?\.pdf)", question, re.IGNORECASE)
    if cv_match:
        cv_path = cv_match.group(1).strip()
        try:
            import sys

            if str(Path.cwd()) not in sys.path:
                sys.path.append(str(Path.cwd()))

            from cv_screening import score_cv

            position_match = re.search(r"cho vị trí (.*?)\.$", question, re.IGNORECASE)
            position = (
                position_match.group(1).strip()
                if position_match
                else "Software Engineer"
            )

            res = score_cv(cv_path, position)
            if "error" not in res:
                return (
                    f"⚠️ **Lưu ý:** Hệ thống đang ở chế độ Offline (Không có API Key).\n"
                    f"Chatbot đã tự động dùng thuật toán tìm kiếm từ khóa cục bộ để chấm điểm CV của bạn:\n\n"
                    f"**Kết quả sơ bộ (Vị trí: {position})**\n"
                    f"- **Điểm:** {res.get('total_score', 0)}/100\n"
                    f"- **Trạng thái:** {res.get('status', 'Unknown')}\n"
                    f"- **Khuyến nghị:** {res.get('action', 'N/A')}\n\n"
                    f"*(Để AI phân tích ngôn ngữ tự nhiên và trích xuất kỹ năng sâu hơn, vui lòng cung cấp API Key)*"
                )
            else:
                return f"Hệ thống đang ở chế độ Offline. Đã nhận file CV ({cv_path}) nhưng không thể đọc: {res['error']}"
        except Exception as e:
            return f"Hệ thống đang ở chế độ Offline. Đã nhận file CV ({cv_path}) nhưng tính năng đánh giá tạm thời không khả dụng. (Lỗi: {e})"

    results = vdb.query("offline_hr_kb", question, n_results=1)

    best_match = None
    if (
        results
        and "metadatas" in results
        and results["metadatas"]
        and len(results["metadatas"][0]) > 0
    ):
        distance = (
            results["distances"][0][0]
            if "distances" in results and results["distances"]
            else 0
        )
        if distance < 0.8:
            best_match = results["metadatas"][0][0].get("answer")

    if best_match:
        if "tôi" in q_lower or "mình" in q_lower or "của tôi" in q_lower:
            prefix = "⚠️ **Lưu ý:** Hệ thống đang ở chế độ Offline nên không thể tra cứu thông tin cá nhân (lương, ngày phép cụ thể của bạn). Dưới đây là chính sách chung của công ty:\n\n"
            return prefix + best_match
        return best_match

    return "Xin lỗi, hiện tại tôi đang ở chế độ Offline và chỉ hỗ trợ được một số câu hỏi có sẵn trong bộ nhớ tạm. Vui lòng thử lại với từ khóa khác!"
