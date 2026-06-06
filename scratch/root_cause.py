import json
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

data = json.load(open('results.json', 'r', encoding='utf-8'))

# ===== PROBLEM 1: doc_name parsing from source_note_text =====
# source_note_text format: "(Điều 1 Luật số 04/2017/QH14 Luật Hỗ trợ doanh nghiệp... có hiệu lực thi hành...)"
# Currently being stored as full string -> doc_name = "có hiệu lực thi hành kể từ" (WRONG!)
# Expected format for scoring: "04/2017/QH14|Luật Hỗ trợ doanh nghiệp nhỏ và vừa"

sample_source_notes = [
    "(Điều 1 Luật số 32/2004/QH11 An ninh Quốc gia ngày 03/12/2004 của Quốc hội, có hiệu lực thi hành kể từ ngày 01/07/2005 )",
    "(Điều 1 Nghị định số 16/2006/NĐ-CP Quy định về việc khôi phục danh dự, đền bù, trợ cấp cho cơ quan, tổ chức, cá nhân bị thiệt hại do tham gia bảo vệ an ninh quốc gia ngày 25/01/2006 của Chính phủ, có hiệu lực thi hành kể từ ngày 15/02/2006)",
    "(Điều 1 Thông tư số 07/2020/TT-BKHCN Quy định về quản lý chương trình phát triển tài sản trí tuệ giai đoạn 2016-2020, có hiệu lực thi hành kể từ ngày 18/08/2020)",
]

print("=== PARSING source_note_text to extract doc_code and doc_name ===")
# Pattern to extract doc_code and doc_name from source_note_text
DOC_CODE_PATTERN = re.compile(
    r'\b(\d{1,3}/\d{4}/(?:QH\d+|NĐ-CP|TT-[A-ZĐ]+(?:-[A-ZĐ]+)*|TTLT-[A-ZĐ]+(?:[-A-ZĐ]+)*|CT-TTg|QĐ-TTg|UBTVQH\d+))\b'
)

def parse_source_note(note: str):
    """Extract doc_code and doc_name from source_note_text."""
    if not note:
        return None, None
    match = DOC_CODE_PATTERN.search(note)
    if not match:
        return None, None
    doc_code = match.group(1)
    # Extract name: text between doc_code and the next date/comma/keyword
    after_code = note[match.end():].strip()
    # Remove date patterns like "ngày 03/12/2004" and trailing content after comma
    name_match = re.match(r'^([^,\n]+?)(?:\s+ngày\s+\d|\s+của\s+(?:Quốc hội|Chính phủ|Bộ)|,)', after_code)
    if name_match:
        doc_name = name_match.group(1).strip()
    else:
        doc_name = after_code[:100].strip()
    return doc_code, doc_name

for note in sample_source_notes:
    code, name = parse_source_note(note)
    print(f"  Input: {note[:80]}...")
    print(f"  Result: code={code}, name={name}")
    print()

# ===== PROBLEM 2: Low top_k =====
print("=== RECALL ANALYSIS ===")
# Current: top_k=5 → max 5 articles per question
# Rank 1 ARTICLES RECALL = 0.6963 vs ours = 0.3547 → NEARLY 2X GAP
# F2 score weights recall 4x → very sensitive to recall

# ===== PROBLEM 3: only legal_statutory, missing caselaw =====
print("=== COVERAGE ANALYSIS ===")
print("System only searches 'legal_statutory' collection")
print("If test questions require caselaw, articles won't be found")

# ===== PROBLEM 4: article_title parsing =====
print("\n=== ARTICLE TITLE PARSING ===")
import pandas as pd
df = pd.read_parquet('data/raw/phapdien_articles.parquet')
print("Sample article_title values:")
for v in df['article_title'].dropna().head(10).tolist():
    print(f"  '{v}'")

print("\nSample source_note_text for SME laws:")
sme_mask = df['topic_title'].str.contains('04/2017|Hỗ trợ doanh nghiệp nhỏ', na=False, case=False)
for _, row in df[sme_mask].head(3).iterrows():
    print(f"  source_note_text: {str(row.get('source_note_text', ''))[:200]}")
    print(f"  article_title: {row.get('article_title', '')}")
    print()
