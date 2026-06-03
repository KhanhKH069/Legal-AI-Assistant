import sys
import os
from pathlib import Path
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent.parent))
RAW_DIR = Path('data/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)

def check_and_install(package: str, import_name: str | None=None):
    import importlib
    name = import_name or package
    try:
        importlib.import_module(name)
    except ImportError:
        print(f'[INFO] Cài thư viện: {package}...')
        os.system(f'{sys.executable} -m pip install {package} -q')
check_and_install('datasets')
check_and_install('pandas')
check_and_install('pyarrow')
from datasets import load_dataset
import pandas as pd

def download_statutory():
    out_path = RAW_DIR / 'phapdien_articles.parquet'
    if out_path.exists():
        print(f'[SKIP] {out_path} already exists. Delete to re-download.')
        df = pd.read_parquet(out_path)
        print(f'  → {len(df):,} articles loaded from cache.')
        return df
    print('\n[1/2] Tải bộ Pháp điển (phapdien-moj-gov-vn)...')
    print('  Dataset: tmquan/phapdien-moj-gov-vn | split: articles')
    try:
        ds = load_dataset('tmquan/phapdien-moj-gov-vn', name='articles', split='train', trust_remote_code=True)
        df = ds.to_pandas()
        df.to_parquet(out_path, index=False)
        print(f'  ✓ Đã tải {len(df):,} điều luật → {out_path}')
        ds_sub = load_dataset('tmquan/phapdien-moj-gov-vn', name='ontology_subjects', split='train', trust_remote_code=True)
        df_sub = ds_sub.to_pandas()
        df_sub.to_parquet(RAW_DIR / 'phapdien_subjects.parquet', index=False)
        print(f"  ✓ Đã tải {len(df_sub):,} chủ đề → {RAW_DIR / 'phapdien_subjects.parquet'}")
        return df
    except Exception as e:
        print(f'  ✗ Lỗi khi tải Pháp điển: {e}')
        raise

def download_caselaw():
    out_path = RAW_DIR / 'anle_documents.parquet'
    if out_path.exists():
        print(f'[SKIP] {out_path} already exists. Delete to re-download.')
        df = pd.read_parquet(out_path)
        print(f'  → {len(df):,} bản án loaded from cache.')
        return df
    print('\n[2/2] Tải bộ Án lệ (anle-toaan-gov-vn)...')
    print('  Dataset: tmquan/anle-toaan-gov-vn | split: documents')
    try:
        ds = load_dataset('tmquan/anle-toaan-gov-vn', name='documents', split='train', trust_remote_code=True)
        df = ds.to_pandas()
        df.to_parquet(out_path, index=False)
        print(f'  ✓ Đã tải {len(df):,} bản án/án lệ → {out_path}')
        return df
    except Exception as e:
        print(f'  ✗ Lỗi khi tải Án lệ: {e}')
        raise

def print_stats(df_stat, df_case):
    print('\n' + '=' * 60)
    print('  THỐNG KÊ DATASETS')
    print('=' * 60)
    print(f'\n📚 Pháp điển (Statutory Law): {len(df_stat):,} điều luật')
    if 'subject_title' in df_stat.columns:
        top_subjects = df_stat['subject_title'].value_counts().head(5)
        print('  Top 5 lĩnh vực:')
        for sub, cnt in top_subjects.items():
            print(f'    - {sub}: {cnt:,} điều')
    print(f'\n⚖️  Án lệ (Case Law): {len(df_case):,} bản án')
    if 'case_type' in df_case.columns:
        top_types = df_case['case_type'].value_counts().head(5)
        print('  Top 5 loại vụ án:')
        for t, cnt in top_types.items():
            if t:
                print(f'    - {t}: {cnt:,} bản án')
    if 'year' in df_case.columns:
        year_range = f"{df_case['year'].min()} - {df_case['year'].max()}"
        print(f'  Năm ban hành: {year_range}')
    print('\n' + '=' * 60)
    print('  ✓ Download hoàn tất! Chạy tiếp:')
    print('    python scripts/index_legal_to_chromadb.py')
    print('=' * 60)
if __name__ == '__main__':
    print('=' * 60)
    print('  LEGAL AI ASSISTANT — Data Downloader')
    print('=' * 60)
    df_statutory = download_statutory()
    df_caselaw = download_caselaw()
    print_stats(df_statutory, df_caselaw)