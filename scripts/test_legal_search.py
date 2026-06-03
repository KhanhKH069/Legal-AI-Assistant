import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ['OFFLINE_MODE'] = 'true'
print('=' * 60)
print('  LEGAL AI ASSISTANT — Quick Search Test')
print('=' * 60)

def test_collections():
    print('\n[1/3] Kiem tra ChromaDB collections...')
    from src.services.vector_db import get_vector_db
    vdb = get_vector_db('./chroma_db')
    collections = vdb.list_collections()
    print(f'  Collections hien co: {collections}')
    for col in ['legal_statutory', 'legal_caselaw']:
        count = vdb.get_collection_count(col)
        status = 'OK' if count > 0 else 'EMPTY'
        print(f'  [{status}] {col}: {count:,} documents')
    return 'legal_statutory' in collections and 'legal_caselaw' in collections

def test_statutory_search():
    print('\n[2/3] Test tra cuu Phap dien...')
    try:
        from src.services.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(collection_name='legal_statutory', persist_directory='./chroma_db', use_reranker=False)
        results = retriever.retrieve('dieu kien ket hon', top_k=2)
        if results:
            print(f'  OK - Tim thay {len(results)} dieu luat')
            for i, r in enumerate(results[:1]):
                meta = r.get('metadata', {})
                print(f"  [{i + 1}] {meta.get('article_title', 'N/A')}")
                print(f"       Subject: {meta.get('subject_title', 'N/A')}")
        else:
            print('  WARN - Khong tim thay ket qua (collection co the chua co du lieu)')
        return True
    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def test_caselaw_search():
    print('\n[3/3] Test tra cuu An le...')
    try:
        from src.services.hybrid_retriever import HybridRetriever
        retriever = HybridRetriever(collection_name='legal_caselaw', persist_directory='./chroma_db', use_reranker=False)
        results = retriever.retrieve('tranh chap dat dai', top_k=2)
        if results:
            print(f'  OK - Tim thay {len(results)} ban an')
            for i, r in enumerate(results[:1]):
                meta = r.get('metadata', {})
                print(f"  [{i + 1}] {meta.get('title', 'N/A')}")
                print(f"       Loai: {meta.get('case_type', 'N/A')} | Nam: {meta.get('year', 'N/A')}")
        else:
            print('  WARN - Khong tim thay ket qua')
        return True
    except Exception as e:
        print(f'  ERROR: {e}')
        return False
if __name__ == '__main__':
    ok1 = test_collections()
    ok2 = test_statutory_search()
    ok3 = test_caselaw_search()
    print('\n' + '=' * 60)
    if ok1 and ok2 and ok3:
        print('  KIEM TRA THANH CONG!')
        print('  Chay backend: uvicorn api.main:app --reload')
    else:
        print('  CO LOI. Chay lai index: python scripts/index_legal_to_chromadb.py --reset')
    print('=' * 60)