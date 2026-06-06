import sys
import re
from pathlib import Path
from tqdm import tqdm
import pandas as pd
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.config import config
from src.services.vector_db import get_vector_db

RAW_DIR = Path('data/raw')

# ─── Regex to extract doc_code from source_note_text ──────────────────────────
_DOC_CODE_RE = re.compile(
    r'\b(\d{1,3}/\d{4}/'
    r'(?:QH\d+|NĐ-CP|TT-[A-ZĐBCTN]+(?:-[A-ZĐBCTN]+)*'
    r'|TTLT-[A-ZĐBCTN]+(?:[-A-ZĐBCTN]+)*'
    r'|CT-TTg|QĐ-TTg|UBTVQH\d+))\b'
)


def _clean_text(val) -> str:
    if pd.isna(val):
        return ''
    return str(val).strip()


def _parse_doc_code_and_name(source_note: str):
    """
    Parse doc_code and doc_name from source_note_text.

    Input:  "(Điều 12 Luật số 04/2017/QH14 Luật Hỗ trợ doanh nghiệp nhỏ và vừa
              ngày 12/06/2017, có hiệu lực thi hành kể từ ngày 01/01/2018)"
    Output: ('04/2017/QH14', 'Luật Hỗ trợ doanh nghiệp nhỏ và vừa')
    """
    if not source_note:
        return '', ''
    m = _DOC_CODE_RE.search(source_note)
    if not m:
        return '', ''
    doc_code = m.group(1)
    # Text AFTER the doc_code, trimmed
    after = source_note[m.end():].strip()
    # Extract doc_name: everything up to "ngày DD/MM...", "của Quốc hội/Chính phủ", or comma
    name_m = re.match(
        r'^([^,\n]+?)(?:\s+ngày\s+\d{1,2}/\d{1,2}|\s+của\s+(?:Quốc hội|Chính phủ|Bộ\s)|,|$)',
        after,
    )
    if name_m:
        doc_name = name_m.group(1).strip()
    else:
        doc_name = after[:120].strip()
    return doc_code, doc_name


def _parse_real_article(article_title: str) -> str:
    """
    Extract the real article number from the phapdien internal code.

    Format: "Điều X.Y.TYPE.Z.N. Title"  →  "Điều N"
    Examples:
      "Điều 1.1.LQ.1. Phạm vi điều chỉnh"   → "Điều 1"
      "Điều 5.1.NĐ.2.7. Điều kiện hỗ trợ"   → "Điều 7"
      "Điều 1.1.NĐ.2.1. Phạm vi..."           → "Điều 1"
    """
    # Match the phapdien code part before the title
    code_m = re.match(r'Điều\s+([\d.A-ZĐNQTL]+?)\.\s', article_title)
    if code_m:
        nums = re.findall(r'\d+', code_m.group(1))
        if nums:
            return f'Điều {nums[-1]}'
    # Fallback: just grab the first number
    fallback = re.search(r'Điều\s+(\d+)', article_title)
    return f'Điều {fallback.group(1)}' if fallback else ''


def _build_doc_name_lookup(df: pd.DataFrame) -> dict:
    """
    First pass: scan the entire parquet to build the best doc_code -> doc_name
    mapping. For each doc_code, keep the longest (most informative) name found.
    """
    lookup: dict = {}
    for note in df['source_note_text'].dropna():
        code, name = _parse_doc_code_and_name(str(note))
        if code and name and len(name) > len(lookup.get(code, '')):
            lookup[code] = name
    print(f'[Lookup] Built doc_name lookup for {len(lookup)} documents.')
    return lookup


def filter_sme_laws(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter articles belonging to the 5 core SME-related laws and their
    implementing regulations (NĐ, TT) that appear in source_note_text.
    """
    # Primary laws
    primary_codes = [
        '04/2017/QH14',   # Luật Hỗ trợ DNNVV
        '59/2020/QH14',   # Luật Doanh nghiệp
        '45/2019/QH14',   # Bộ luật Lao động
        '14/2008/QH12',   # Luật TNDN
        '58/2014/QH13',   # Luật BHXH
        '41/2024/QH15',   # Luật BHXH (sửa đổi)
    ]
    # Key implementing regulations
    impl_codes = [
        '76/2018/NĐ-CP',   # Hướng dẫn Luật Hỗ trợ DNNVV
        '94/2020/NĐ-CP',   # Trung tâm Đổi mới sáng tạo
        '80/2021/NĐ-CP',   # Quy định chi tiết Luật Hỗ trợ DNNVV
        '12/2022/NĐ-CP',   # Xử phạt vi phạm lao động
        '145/2020/NĐ-CP',  # Hướng dẫn Bộ luật Lao động
        '38/2022/NĐ-CP',   # Lương tối thiểu
        '91/2022/NĐ-CP',   # BHXH
        '07/2020/TT-BKHCN', # Ươm tạo công nghệ
        '219/2013/TT-BTC', # Thuế GTGT
        '78/2014/TT-BTC',  # Thuế TNDN
    ]
    name_keywords = [
        'Hỗ trợ doanh nghiệp nhỏ và vừa',
        'Luật Doanh nghiệp',
        'Bộ luật Lao động',
        'Thuế thu nhập doanh nghiệp',
        'Bảo hiểm xã hội',
    ]
    all_keywords = primary_codes + impl_codes + name_keywords
    pattern = '|'.join(re.escape(kw) for kw in all_keywords)
    mask = (
        df['topic_title'].str.contains(pattern, case=False, na=False)
        | df['subject_title'].str.contains(pattern, case=False, na=False)
        | df['source_note_text'].str.contains(pattern, case=False, na=False)
    )
    return df[mask]


def index_sme_laws():
    parquet_path = RAW_DIR / 'phapdien_articles.parquet'
    if not parquet_path.exists():
        print(f'[ERROR] {parquet_path} does not exist. Run download_datasets.py first.')
        return

    print('Loading parquet file...')
    df = pd.read_parquet(parquet_path)
    print(f'Total articles in Phapdien: {len(df):,}')

    # ── Pass 1: Build best doc_name lookup from entire dataset ────────────────
    print('Building doc_name lookup table (pass 1/2)...')
    doc_name_lookup = _build_doc_name_lookup(df)

    sme_df = filter_sme_laws(df)
    print(f'Total SME articles found: {len(sme_df):,}')
    if len(sme_df) == 0:
        print('No matching articles found. Aborting.')
        return

    vdb = get_vector_db()
    col_name = config.statutory_collection
    print(f"\nResetting collection '{col_name}' in ChromaDB...")
    try:
        vdb.client.delete_collection(name=col_name)
    except Exception as e:
        print(f'Notice: Could not delete collection (may not exist yet): {e}')

    # Stats counters
    parsed_ok = 0
    parsed_fail = 0

    BATCH = 50
    for start in tqdm(range(0, len(sme_df), BATCH), desc='Indexing SME Laws'):
        batch = sme_df.iloc[start:start + BATCH]
        documents, metadatas, ids = [], [], []

        for row in batch.itertuples(index=True):
            content_text  = _clean_text(getattr(row, 'content_text', None))
            article_title = _clean_text(getattr(row, 'article_title', None))
            chapter_title = _clean_text(getattr(row, 'chapter_title', None))
            subject_title = _clean_text(getattr(row, 'subject_title', None))
            topic_title   = _clean_text(getattr(row, 'topic_title', None))
            source_note   = _clean_text(getattr(row, 'source_note_text', None))
            source_url    = _clean_text(getattr(row, 'source_url', None))

            if not content_text:
                continue

            # ── Parse citation fields ──────────────────────────────────────────
            doc_code, doc_name = _parse_doc_code_and_name(source_note)
            # Fill empty/short doc_name from lookup table
            if doc_code and (not doc_name or len(doc_name) < 10):
                doc_name = doc_name_lookup.get(doc_code, doc_name)
            real_article = _parse_real_article(article_title)

            if doc_code:
                parsed_ok += 1
            else:
                parsed_fail += 1

            # ── Build text blob for embedding ─────────────────────────────────
            text_blob = (
                f'Chủ đề: {topic_title}\n'
                f'Đề mục: {subject_title}\n'
                f'Chương: {chapter_title}\n'
                f'Điều: {article_title}\n'
                f'Nội dung:\n{content_text}'
            )
            if source_note:
                text_blob += f'\nNguồn: {source_note}'
            text_blob = text_blob[:4000]

            # ── Metadata (now includes citation fields) ────────────────────────
            meta = {
                # Citation fields — used by build_citations_from_metadata()
                'doc_code':     doc_code,
                'doc_name':     doc_name,
                'real_article': real_article,
                # Human-readable fields
                'article_title': article_title or 'Không rõ',
                'chapter_title': chapter_title or '',
                'subject_title': subject_title or '',
                'topic_title':   topic_title or '',
                'source_url':    source_url or '',
                'source_note':   source_note[:500] if source_note else '',
                'law_type':      'statutory',
            }

            doc_id = f'sme_law_{start}_{row.Index}'
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)

        if documents:
            try:
                col = vdb.create_collection(col_name)
                col.add(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                print(f'Error adding batch {start}: {e}')

    print(f'\n✅ Citation metadata parsed: {parsed_ok:,} OK / {parsed_fail:,} failed')

    print('\nBuilding BM25 keyword index (for Hybrid Search)...')
    from src.services.hybrid_retriever import get_hybrid_retriever
    retriever = get_hybrid_retriever(col_name)
    retriever.build_bm25()
    print('BM25 index built successfully.')
    print(f'\nDone! Indexed {len(sme_df):,} SME law articles into ChromaDB.')


if __name__ == '__main__':
    index_sme_laws()