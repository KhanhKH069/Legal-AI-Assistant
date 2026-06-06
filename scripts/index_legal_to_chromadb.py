import argparse
import sys
import re
from pathlib import Path
import hashlib
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))
RAW_DIR = Path('data/raw')
CHROMA_DIR = './chroma_db'

KNOWN_LAW_NAMES = {
    '59/2020/QH14': 'Luật Doanh nghiệp',
    '04/2017/QH14': 'Luật Hỗ trợ doanh nghiệp nhỏ và vừa',
    '67/2014/QH13': 'Luật Doanh nghiệp',
    '09/2012/QH13': 'Luật Lao động',
    '45/2019/QH14': 'Bộ luật Lao động',
    '91/2015/QH13': 'Bộ luật Dân sự',
    '05/2020/QH14': 'Luật Doanh nghiệp',
    '02/2011/QH13': 'Luật Khiếu nại',
    '97/2015/QH13': 'Luật Phí và lệ phí',
    '57/2010/QH12': 'Luật Thuế',
    '81/2006/QH11': 'Luật Cư trú',
    '32/2004/QH11': 'Luật An ninh Quốc gia',
}

def parse_source_note(source_note: str) -> dict:
    """Parse source_note_text to extract doc_code, doc_name, and real_article.
    Example input: (Điều 14 Luật số 59/2020/QH14 Luật Doanh nghiệp ngày...)
    Returns: {'doc_code': '59/2020/QH14', 'doc_name': 'Luật Doanh nghiệp', 'real_article': 'Điều 14'}
    """
    result = {'doc_code': '', 'doc_name': '', 'real_article': ''}
    if not source_note:
        return result

    art_match = re.search(r'Đi[eề]u\s+([\d]+[a-zA-Z]*)', source_note)
    if art_match:
        result['real_article'] = f'Điều {art_match.group(1)}'

    code_pattern = r'(?:Luật số|Nghị định số|Thông tư số|Quyết định số|Nghị quyết số|Thông tư liên tịch số)\s+([\w/\-\.]+)'
    code_match = re.search(code_pattern, source_note)
    if code_match:
        raw_code = code_match.group(1).rstrip(',.)')
        result['doc_code'] = raw_code
        if raw_code in KNOWN_LAW_NAMES:
            result['doc_name'] = KNOWN_LAW_NAMES[raw_code]
        else:
            name_pattern = rf'{re.escape(raw_code)}[,\s]+(.+?)(?=\s+ngày|\s+của\s+|\s*,\s*có hiệu lực|\s*\)$)'
            name_match = re.search(name_pattern, source_note)
            if name_match:
                result['doc_name'] = name_match.group(1).strip().rstrip(',.)')

    return result

def _build_chroma_client():
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(anonymized_telemetry=False, allow_reset=True))
    try:
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='truro7/vn-law-embedding')
        print('[INDEX] Using embedding: truro7/vn-law-embedding')
    except Exception:
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='dangvantuan/vietnamese-document-embedding')
        print('[INDEX] Using embedding: dangvantuan/vietnamese-document-embedding (fallback)')
    return (client, emb_fn)
_client = None
_emb_fn = None

def _get_or_create_collection(name: str, reset: bool=False):
    global _client, _emb_fn
    if _client is None:
        _client, _emb_fn = _build_chroma_client()
    if reset:
        try:
            _client.delete_collection(name)
            print(f'  -> Xoa collection cu: {name}')
        except Exception:
            pass
    return _client.get_or_create_collection(name=name, metadata={'hnsw:space': 'cosine'}, embedding_function=_emb_fn)

def _add_documents_direct(collection_name: str, documents, metadatas, ids, reset: bool=False):
    col = _get_or_create_collection(collection_name, reset=False)
    col.add(documents=documents, metadatas=metadatas, ids=ids)
    return len(documents)

def _clean_text(text) -> str:
    if text is None:
        return ''
    s = str(text).strip()
    return s if s else ''

def _make_id(prefix: str, row_idx: int, extra: str='') -> str:
    raw = f'{prefix}_{row_idx}_{extra}'
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def index_statutory(max_rows=None, reset: bool=False):
    import pandas as pd
    parquet_path = RAW_DIR / 'phapdien_articles.parquet'
    if not parquet_path.exists():
        print(f'[ERROR] {parquet_path} khong ton tai. Chay download_datasets.py truoc.')
        return 0
    print('\n[1/2] Indexing Phap dien -> collection: legal_statutory ...')
    df = pd.read_parquet(parquet_path)
    if max_rows:
        df = df.head(max_rows)
    print(f'  So dieu luat se index: {len(df):,}')
    col = _get_or_create_collection('legal_statutory', reset=reset)
    BATCH = 100
    total_indexed = 0
    for start in range(0, len(df), BATCH):
        batch = df.iloc[start:start + BATCH]
        documents, metadatas, ids = ([], [], [])
        for idx, row in batch.iterrows():
            content_text = _clean_text(row.get('content_text'))
            article_title = _clean_text(row.get('article_title'))
            chapter_title = _clean_text(row.get('chapter_title'))
            subject_title = _clean_text(row.get('subject_title'))
            topic_title = _clean_text(row.get('topic_title'))
            source_note = _clean_text(row.get('source_note_text'))
            source_url = _clean_text(row.get('source_url'))
            if not content_text:
                continue
            parsed = parse_source_note(source_note)
            doc_code = parsed['doc_code']
            doc_name = parsed['doc_name']
            real_article = parsed['real_article']
            text_blob = f'Chủ đề: {topic_title}\nĐề mục: {subject_title}\nChương: {chapter_title}\nĐiều: {article_title}\nNội dung:\n{content_text}'
            if source_note:
                text_blob += f'\nNguồn: {source_note}'
            text_blob = text_blob[:4000]
            meta = {
                'article_title': article_title or 'Không rõ',
                'chapter_title': chapter_title or '',
                'subject_title': subject_title or '',
                'topic_title': topic_title or '',
                'source_url': source_url or '',
                'source_note': source_note[:500] if source_note else '',
                'doc_code': doc_code,
                'doc_name': doc_name,
                'real_article': real_article,
                'data_type': 'statutory',
            }
            doc_id = _make_id('stat', int(idx), article_title)
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)
        if documents:
            try:
                col.add(documents=documents, metadatas=metadatas, ids=ids)
                total_indexed += len(documents)
            except Exception as e:
                print(f'  [WARN] Batch {start}-{start + BATCH}: {e}')
        pct = min(100, int((start + BATCH) / len(df) * 100))
        print(f'  Progress: {pct}% ({total_indexed:,} docs indexed)...', end='\r')
    print(f'\n  OK - Da index {total_indexed:,} dieu luat vao [legal_statutory]')
    return total_indexed

def index_caselaw(max_rows=None, reset: bool=False):
    import pandas as pd
    parquet_path = RAW_DIR / 'anle_documents.parquet'
    if not parquet_path.exists():
        print(f'[ERROR] {parquet_path} khong ton tai. Chay download_datasets.py truoc.')
        return 0
    print('\n[2/2] Indexing An le -> collection: legal_caselaw ...')
    df = pd.read_parquet(parquet_path)
    if max_rows:
        df = df.head(max_rows)
    print(f'  So ban an se index: {len(df):,}')
    col = _get_or_create_collection('legal_caselaw', reset=reset)
    BATCH = 50
    total_indexed = 0
    for start in range(0, len(df), BATCH):
        batch = df.iloc[start:start + BATCH]
        documents, metadatas, ids = ([], [], [])
        for idx, row in batch.iterrows():
            doc_name = _clean_text(row.get('doc_name'))
            title = _clean_text(row.get('title'))
            subject = _clean_text(row.get('subject'))
            case_type = _clean_text(row.get('case_type'))
            doc_subtype = _clean_text(row.get('doc_subtype'))
            year = str(row.get('year', '')) if row.get('year') else ''
            markdown = _clean_text(row.get('markdown'))
            principle_text = _clean_text(row.get('principle_text'))
            issuing_authority = _clean_text(row.get('issuing_authority'))
            court_level = _clean_text(row.get('court_level'))
            detail_url = _clean_text(row.get('detail_url'))
            applied_article = _clean_text(row.get('applied_article_code'))
            precedent_num = _clean_text(row.get('precedent_number'))
            primary_text = principle_text if principle_text else markdown
            if not primary_text:
                continue
            text_blob = f'Tên bản án: {title or doc_name}\nLoại vụ án: {case_type} - {doc_subtype}\nLĩnh vực: {subject}\nTòa án: {issuing_authority} ({court_level})\nNăm: {year}\nĐiều luật áp dụng: {applied_article}\nNguyên tắc pháp lý:\n{primary_text}'
            if precedent_num:
                text_blob = f'Án lệ số: {precedent_num}\n' + text_blob
            text_blob = text_blob[:6000]
            meta = {'doc_name': doc_name or title or '', 'title': title or '', 'case_type': case_type or '', 'doc_subtype': doc_subtype or '', 'subject': subject or '', 'year': year or '', 'court_level': court_level or '', 'detail_url': detail_url or '', 'applied_article': applied_article or '', 'precedent_number': precedent_num or '', 'data_type': 'caselaw'}
            doc_id = _make_id('case', int(idx), doc_name)
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)
        if documents:
            try:
                col.add(documents=documents, metadatas=metadatas, ids=ids)
                total_indexed += len(documents)
            except Exception as e:
                print(f'  [WARN] Batch {start}-{start + BATCH}: {e}')
        pct = min(100, int((start + BATCH) / len(df) * 100))
        print(f'  Progress: {pct}% ({total_indexed:,} docs indexed)...', end='\r')
    print(f'\n  OK - Da index {total_indexed:,} ban an vao [legal_caselaw]')
    return total_indexed

def main():
    parser = argparse.ArgumentParser(description='Index legal datasets into ChromaDB')
    parser.add_argument('--max-statutory', type=int, default=None)
    parser.add_argument('--max-caselaw', type=int, default=None)
    parser.add_argument('--reset', action='store_true', help='Delete old collections before re-indexing')
    args = parser.parse_args()
    print('=' * 60)
    print('  LEGAL AI ASSISTANT - ChromaDB Indexer (Local Embeddings)')
    print('=' * 60)
    _get_or_create_collection('legal_statutory', reset=False)
    n1 = index_statutory(max_rows=args.max_statutory, reset=args.reset)
    n2 = index_caselaw(max_rows=args.max_caselaw, reset=args.reset)
    print('\n' + '=' * 60)
    print('  Indexing DONE')
    print(f'  legal_statutory : {n1:,} documents')
    print(f'  legal_caselaw   : {n2:,} documents')
    print('=' * 60)
    print('  Next: uvicorn api.main:app --reload')
    print('=' * 60)
if __name__ == '__main__':
    main()