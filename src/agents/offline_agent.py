"""Simple offline QA agent that uses local markdown files."""
from pathlib import Path
import re
from typing import List, Tuple

# paths to markdown knowledge‑base files
# add additional docs here (HR policies, FAQs, etc.)
KB_FILES = [
    Path("documents/01_HR_Policies.md"),
    Path("documents/04_Onboarding.md"),
]

qa_pairs: List[Tuple[str, str]] = []


def _load_kb():
    global qa_pairs
    qa_pairs = []
    for path in KB_FILES:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # parse headings Qn: and answers until next ---
        entries = re.split(r"\n---+\n", text)
        for entry in entries:
            lines = entry.strip().splitlines()
            if not lines:
                continue
            # look for question line
            qline = None
            ans_lines = []
            for line in lines:
                if line.startswith("### Q"):
                    continue
                if line.startswith("**Câu hỏi:**"):
                    qline = line.replace("**Câu hỏi:**", "").strip()
                elif qline is not None:
                    # skip variant metadata and trim the answer label
                    if line.startswith("**Biến thể:"):
                        continue
                    if line.startswith("**Trả lời:"):
                        ans_lines.append(line.replace("**Trả lời:", "").strip())
                    else:
                        ans_lines.append(line)
            if qline and ans_lines:
                answer = "\n".join(ans_lines).strip()
                qa_pairs.append((qline, answer))
    # debugging: show how many Q&A pairs were loaded
    # (this will print on first request)
    if qa_pairs:
        print(f"[OFFLINE_AGENT] loaded {len(qa_pairs)} QA pairs from KB files")


def answer_question(question: str) -> str:
    """Return the best matching answer from the loaded knowledge base."""
    if not qa_pairs:
        _load_kb()
    q_lower = question.lower()
    # simple substring match of question text or keywords
    for q, a in qa_pairs:
        if q_lower in q.lower():
            return a
    # fallback: try any keyword match
    for q, a in qa_pairs:
        for word in q.lower().split():
            if word in q_lower and len(word) > 3:
                return a
    return "Xin lỗi, tôi chưa biết câu trả lời cho câu hỏi đó."