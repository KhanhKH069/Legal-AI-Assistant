import sys
import re
from pathlib import Path
from tqdm import tqdm
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.config import config
from src.services.vector_db import get_vector_db
RAW_DIR = Path('data/raw')

def _clean_text(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

def filter_sme_laws(df: pd.DataFrame) -> pd.DataFrame:
    keywords = ['04/2017/QH14', 'Hỗ trợ doanh nghiệp nhỏ và vừa', '59/2020/QH14', 'Luật Doanh nghiệp', '45/2019/QH14', 'Bộ luật Lao động', '14/2008/QH12', 'Thuế thu nhập doanh nghiệp', '58/2014/QH13', '41/2024/QH15', 'Bảo hiểm xã hội']
    pattern = '|'.join([re.escape(kw) for kw in keywords])
    mask = df['topic_title'].str.contains(pattern, case=False, na=False) | df['subject_title'].str.contains(pattern, case=False, na=False) | df['source_note_text'].str.contains(pattern, case=False, na=False)
    return df[mask]

def index_sme_laws():
    parquet_path = RAW_DIR / 'phapdien_articles.parquet'
    if not parquet_path.exists():
        print(f'[ERROR] {parquet_path} does not exist. Run download_datasets.py first.')
        return
    print('Loading parquet file (this may take a moment)...')
    df = pd.read_parquet(parquet_path)
    print(f'Total articles in Phapdien: {len(df):,}')
    sme_df = filter_sme_laws(df)
    print(f'Total SME articles found: {len(sme_df):,}')
    if len(sme_df) == 0:
        print('No matching articles found. Aborting.')
        return
    vdb = get_vector_db()
    col_name = config.statutory_collection
    print(f"\nResetting collection '{col_name}' in ChromaDB to ensure clean state...")
    try:
        vdb.client.delete_collection(name=col_name)
    except Exception as e:
        print(f'Notice: Could not delete collection (might not exist yet): {e}')
    BATCH = 50
    for start in tqdm(range(0, len(sme_df), BATCH), desc='Indexing SME Laws'):
        batch = sme_df.iloc[start:start + BATCH]
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
            text_blob = f'Chủ đề: {topic_title}\nĐề mục: {subject_title}\nChương: {chapter_title}\nĐiều: {article_title}\nNội dung:\n{content_text}'
            if source_note:
                text_blob += f'\nNguồn: {source_note}'
            text_blob = text_blob[:4000]
            meta = {'article_title': article_title or 'Không rõ', 'chapter_title': chapter_title or '', 'subject_title': subject_title or '', 'topic_title': topic_title or '', 'source_url': source_url or '', 'source_note': source_note[:500] if source_note else '', 'law_type': 'statutory'}
            doc_id = f'sme_law_{start}_{idx}'
            documents.append(text_blob)
            metadatas.append(meta)
            ids.append(doc_id)
        if documents:
            try:
                col = vdb.client.get_or_create_collection(col_name)
                col.add(documents=documents, metadatas=metadatas, ids=ids)
            except Exception as e:
                print(f'Error adding batch {start}: {e}')
    print('\nBuilding BM25 keyword index (for Hybrid Search)...')
    from src.services.hybrid_retriever import get_hybrid_retriever
    retriever = get_hybrid_retriever(col_name)
    retriever.build_bm25()
    print('BM25 index built successfully.')
    print('\nDone! Indexed', len(sme_df), 'SME law articles into ChromaDB.')
if __name__ == '__main__':
    index_sme_laws()