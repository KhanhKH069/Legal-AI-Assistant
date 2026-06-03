import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.services.graph_db import get_graph_db

def clean_text(text) -> str:
    if text is None:
        return ''
    return str(text).strip()

def main():
    try:
        import pandas as pd
    except ImportError:
        print('Vui lòng cài đặt pandas và pyarrow (uv pip install pandas pyarrow)')
        return
    parquet_path = Path('data/raw/phapdien_articles.parquet')
    if not parquet_path.exists():
        print(f'File không tồn tại: {parquet_path}')
        return
    print('Đang đọc dữ liệu Parquet...')
    df = pd.read_parquet(parquet_path)
    db = get_graph_db()
    if not db.driver:
        print('Không thể kết nối Neo4j. Vui lòng đảm bảo container neo4j đang chạy.')
        return
    print('Đang tạo Constraints trong Neo4j...')
    db.query('CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE')
    db.query('CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subject) REQUIRE s.name IS UNIQUE')
    db.query('CREATE CONSTRAINT IF NOT EXISTS FOR (c:Chapter) REQUIRE c.name IS UNIQUE')
    db.query('CREATE CONSTRAINT IF NOT EXISTS FOR (a:Article) REQUIRE a.id IS UNIQUE')
    total = len(df)
    print(f'Bắt đầu đẩy {total} điều luật vào Neo4j...')
    query = '\n    MERGE (topic:Topic {name: $topic_title})\n    MERGE (subject:Subject {name: $subject_title})\n    MERGE (topic)-[:HAS_SUBJECT]->(subject)\n\n    MERGE (chapter:Chapter {name: $chapter_title})\n    MERGE (subject)-[:HAS_CHAPTER]->(chapter)\n\n    MERGE (article:Article {id: $article_id})\n    SET article.title = $article_title,\n        article.content = $content_text,\n        article.source_url = $source_url\n\n    MERGE (chapter)-[:HAS_ARTICLE]->(article)\n    '
    for i, row in df.iterrows():
        topic = clean_text(row.get('topic_title')) or 'Chưa phân loại'
        subject = clean_text(row.get('subject_title')) or 'Chưa phân loại'
        chapter = clean_text(row.get('chapter_title')) or 'Chưa phân loại'
        article_title = clean_text(row.get('article_title')) or f'Điều {i}'
        content = clean_text(row.get('content_text'))
        source_url = clean_text(row.get('source_url'))
        article_id = f'{topic}_{subject}_{chapter}_{article_title}'
        params = {'topic_title': topic, 'subject_title': subject, 'chapter_title': chapter, 'article_title': article_title, 'content_text': content, 'source_url': source_url, 'article_id': article_id}
        db.query(query, params)
        if (i + 1) % 100 == 0:
            print(f'Đã xử lý: {i + 1}/{total}')
    print('Hoàn tất đẩy dữ liệu vào Neo4j!')
    db.close()
if __name__ == '__main__':
    main()