import sys
from pathlib import Path
from tqdm import tqdm
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.config import config
from src.services.vector_db import get_vector_db
RAW_DIR = Path('data/raw')

def _clean(val) -> str:
    if pd.isna(val):
        return ''
    return str(val).strip()

def index_caselaw():
    parquet_path = RAW_DIR / 'anle_documents.parquet'
    if not parquet_path.exists():
        print(f'[ERROR] {parquet_path} not found. Run download_datasets.py first.')
        return
    print('Loading caselaw parquet...')
    df = pd.read_parquet(parquet_path)
    print(f'Total case law documents: {len(df):,}')
    vdb = get_vector_db()
    col_name = config.caselaw_collection
    print(f"\nResetting collection '{col_name}'...")
    try:
        vdb.client.delete_collection(name=col_name)
    except Exception:
        pass
    BATCH = 50
    for start in tqdm(range(0, len(df), BATCH), desc='Indexing Case Law'):
        batch = df.iloc[start:start + BATCH]
        documents, metadatas, ids = ([], [], [])
        for idx, row in batch.iterrows():
            content = _clean(row.get('markdown') or row.get('text') or '')
            if not content:
                continue
            title = _clean(row.get('title') or row.get('doc_name') or '')
            case_type = _clean(row.get('case_type') or '')
            court = _clean(row.get('court_level') or '')
            year = str(int(row['year'])) if pd.notna(row.get('year')) else ''
            precedent_num = _clean(row.get('precedent_number') or '')
            detail_url = _clean(row.get('detail_url') or '')
            applied_article = _clean(row.get('applied_article_code') or row.get('applied_article_number') or '')
            text_blob = f'Tieu de: {title}\nLoai vu an: {case_type}\nToa: {court}\nNam: {year}\n'
            if applied_article:
                text_blob += f'Dieu luat ap dung: {applied_article}\n'
            text_blob += f'Noi dung:\n{content}'
            text_blob = text_blob[:4000]
            meta = {'title': title or 'Ban an', 'case_type': case_type, 'court_level': court, 'year': year, 'precedent_number': precedent_num, 'detail_url': detail_url, 'applied_article': applied_article, 'law_type': 'caselaw'}
            doc_id = f'caselaw_{start}_{idx}'
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)
        if documents:
            try:
                col = vdb.client.get_or_create_collection(col_name)
                col.add(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                print(f'Error adding batch {start}: {e}')
    print('\nBuilding BM25 index for case law...')
    from src.services.hybrid_retriever import get_hybrid_retriever
    retriever = get_hybrid_retriever(col_name)
    retriever.build_bm25()
    print('BM25 built.')
    final_col = vdb.client.get_collection(col_name)
    print(f'\nDone! Indexed {final_col.count():,} case law documents.')
if __name__ == '__main__':
    index_caselaw()