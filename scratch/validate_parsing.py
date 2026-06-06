"""
Kiểm tra nhanh logic parsing doc_code, doc_name, real_article
trước khi re-index toàn bộ ChromaDB.
"""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

# ── Copy exact functions từ index_sme_laws.py ─────────────────────────────────
_DOC_CODE_RE = re.compile(
    r'\b(\d{1,3}/\d{4}/'
    r'(?:QH\d+|NĐ-CP|TT-[A-ZĐBCTN]+(?:-[A-ZĐBCTN]+)*'
    r'|TTLT-[A-ZĐBCTN]+(?:[-A-ZĐBCTN]+)*'
    r'|CT-TTg|QĐ-TTg|UBTVQH\d+))\b'
)

def _parse_doc_code_and_name(source_note: str):
    if not source_note:
        return '', ''
    m = _DOC_CODE_RE.search(source_note)
    if not m:
        return '', ''
    doc_code = m.group(1)
    after = source_note[m.end():].strip()
    name_m = re.match(
        r'^([^,\n]+?)(?:\s+ngày\s+\d{1,2}/\d{1,2}|\s+của\s+(?:Quốc hội|Chính phủ|Bộ\s)|,|$)',
        after,
    )
    doc_name = name_m.group(1).strip() if name_m else after[:120].strip()
    return doc_code, doc_name

def _parse_real_article(article_title: str) -> str:
    code_m = re.match(r'Điều\s+([\d.A-ZĐNQTL]+?)\.\s', article_title)
    if code_m:
        nums = re.findall(r'\d+', code_m.group(1))
        if nums:
            return f'Điều {nums[-1]}'
    fallback = re.search(r'Điều\s+(\d+)', article_title)
    return f'Điều {fallback.group(1)}' if fallback else ''

# ── Test cases ─────────────────────────────────────────────────────────────────
source_notes = [
    "(Điều 1 Luật số 32/2004/QH11 An ninh Quốc gia ngày 03/12/2004 của Quốc hội, có hiệu lực thi hành kể từ ngày 01/07/2005 )",
    "(Điều 12 Luật số 04/2017/QH14 Luật Hỗ trợ doanh nghiệp nhỏ và vừa ngày 12/06/2017, có hiệu lực thi hành kể từ ngày 01/01/2018)",
    "(Điều 1 Nghị định số 76/2018/NĐ-CP Quy định chi tiết và hướng dẫn thi hành một số điều của Luật Hỗ trợ doanh nghiệp nhỏ và vừa ngày 15/05/2018 của Chính phủ, có hiệu lực thi hành kể từ ngày 01/07/2018)",
    "(Điều 5 Thông tư số 07/2020/TT-BKHCN Quy định về quản lý chương trình phát triển tài sản trí tuệ giai đoạn 2016-2020, có hiệu lực thi hành kể từ ngày 18/08/2020)",
    "(Điều 9 Nghị định số 94/2020/NĐ-CP Quy định cơ chế, chính sách ưu đãi đối với Trung tâm Đổi mới sáng tạo Quốc gia ngày 21/08/2020 của Chính phủ, có hiệu lực thi hành kể từ ngày 07/10/2020)",
    "(Điều 7 Thông tư liên tịch số 02/2018/TTLT-VKSTC-TATC-BCA-BQP-BTC-BNN Về phối hợp thi hành một số quy định, có hiệu lực thi hành kể từ ngày 15/02/2018)",
    "Đây là điều không có doc_code",
    "",
]

article_titles = [
    "Điều 1.1.LQ.1. Phạm vi điều chỉnh",
    "Điều 1.1.NĐ.1.1. Phạm vi điều chỉnh",
    "Điều 5.1.NĐ.2.7. Điều kiện hỗ trợ",
    "Điều 3.2.TT.1.12. Quy định về hồ sơ",
    "Điều 12.1.LQ.5. Hỗ trợ mặt bằng",
    "Điều không có số",
]

print("=" * 70)
print("TEST: _parse_doc_code_and_name()")
print("=" * 70)
ok = fail = 0
for note in source_notes:
    code, name = _parse_doc_code_and_name(note)
    status = "✅" if code else "❌"
    if code: ok += 1
    else: fail += 1
    name_short = name[:50]
    print(f"{status} code={code!r:30s}  name={name_short!r}")
    note_short = note[:80]
    print(f"   input={note_short!r}")
    print()

print(f"Result: {ok} parsed / {fail} failed\n")

print("=" * 70)
print("TEST: _parse_real_article()")
print("=" * 70)
expected = ["Điều 1", "Điều 1", "Điều 7", "Điều 12", "Điều 5", ""]
for title, exp in zip(article_titles, expected):
    result = _parse_real_article(title)
    status = "✅" if result == exp else "❌"
    print(f"{status} '{title}' → '{result}' (expected: '{exp}')")

# ── Sanity check on real parquet data ─────────────────────────────────────────
print("\n" + "=" * 70)
print("SANITY CHECK: Real parquet data")
print("=" * 70)
try:
    import pandas as pd
    df = pd.read_parquet('data/raw/phapdien_articles.parquet')
    sample = df.dropna(subset=['source_note_text']).head(20)
    ok2 = fail2 = 0
    for _, row in sample.iterrows():
        code, name = _parse_doc_code_and_name(str(row['source_note_text']))
        if code:
            ok2 += 1
        else:
            fail2 += 1
    print(f"Sample 20 rows: {ok2} parsed / {fail2} failed")

    # Test on SME law articles specifically
    mask = df['source_note_text'].str.contains('04/2017/QH14', na=False)
    sme_sample = df[mask].head(5)
    print(f"\nSME law sample (04/2017/QH14):")
    for _, row in sme_sample.iterrows():
        note = str(row.get('source_note_text', ''))
        title = str(row.get('article_title', ''))
        code, name = _parse_doc_code_and_name(note)
        art = _parse_real_article(title)
        print(f"  doc_code={code!r}, doc_name={name[:40]!r}, real_article={art!r}")
except Exception as e:
    print(f"Could not read parquet: {e}")
