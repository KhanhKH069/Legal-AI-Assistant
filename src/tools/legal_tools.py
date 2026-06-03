from langchain_core.tools import tool
from src.services.hybrid_retriever import get_hybrid_retriever
from src.services.graph_db import get_graph_db
from duckduckgo_search import DDGS

def _get_statutory_retriever():
    return get_hybrid_retriever('legal_statutory')

def _get_caselaw_retriever():
    return get_hybrid_retriever('legal_caselaw')

def _get_qa_retriever():
    return get_hybrid_retriever('legal_qa')

@tool
def search_statutory_law(query: str, top_k: int=5) -> str:
    try:
        retriever = _get_statutory_retriever()
        results = retriever.retrieve(query, top_k=top_k)
        if not results:
            return 'Không tìm thấy điều luật liên quan trong Hệ thống Pháp điển. Hãy thử diễn đạt câu hỏi theo cách khác.'
        parts = [f'**KẾT QUẢ TRA CỨU PHÁP ĐIỂN** (Top {len(results)} kết quả):\n']
        for i, r in enumerate(results, 1):
            meta = r.get('metadata', {})
            content = r.get('content', '')
            citation_parts = []
            if meta.get('article_title'):
                citation_parts.append(meta['article_title'])
            if meta.get('chapter_title'):
                citation_parts.append(meta['chapter_title'])
            if meta.get('subject_title'):
                citation_parts.append(meta['subject_title'])
            if meta.get('topic_title'):
                citation_parts.append(meta['topic_title'])
            citation = ' | '.join(citation_parts) if citation_parts else 'Pháp điển'
            source_url = meta.get('source_url', '')
            source_note = meta.get('source_note', '')
            parts.append(f'[{i}] **{citation}**')
            if source_note:
                parts.append(f'    Nguồn: {source_note}')
            if source_url:
                parts.append(f'    🔗 Link: {source_url}')
            parts.append(f'    {content[:800].strip()}')
            parts.append('')
        return '\n'.join(parts)
    except Exception as e:
        return f"Lỗi khi tra cứu Pháp điển: {str(e)}. Kiểm tra lại collection 'legal_statutory' đã được index chưa."

@tool
def search_case_law(query: str, top_k: int=5) -> str:
    try:
        retriever = _get_caselaw_retriever()
        results = retriever.retrieve(query, top_k=top_k)
        if not results:
            return 'Không tìm thấy án lệ liên quan. Hãy thử mô tả tình huống tranh chấp cụ thể hơn.'
        parts = [f'**KẾT QUẢ TRA CỨU ÁN LỆ** (Top {len(results)} kết quả):\n']
        for i, r in enumerate(results, 1):
            meta = r.get('metadata', {})
            content = r.get('content', '')
            title = meta.get('title') or meta.get('doc_name') or 'Bản án'
            case_type = meta.get('case_type', '')
            court = meta.get('court_level', '')
            year = meta.get('year', '')
            precedent_num = meta.get('precedent_number', '')
            detail_url = meta.get('detail_url', '')
            applied_article = meta.get('applied_article', '')
            header = f'[{i}] **{title}**'
            if precedent_num:
                header = f'[{i}] **Án lệ số {precedent_num} — {title}**'
            parts.append(header)
            info_parts = []
            if case_type:
                info_parts.append(f'Loại: {case_type}')
            if court:
                info_parts.append(f'Tòa: {court}')
            if year:
                info_parts.append(f'Năm: {year}')
            if applied_article:
                info_parts.append(f'Điều luật áp dụng: {applied_article}')
            if info_parts:
                parts.append(f"    📋 {' | '.join(info_parts)}")
            if detail_url:
                parts.append(f'    🔗 Nguồn: {detail_url}')
            parts.append(f'    {content[:1000].strip()}')
            parts.append('')
        return '\n'.join(parts)
    except Exception as e:
        return f"Lỗi khi tra cứu Án lệ: {str(e)}. Kiểm tra lại collection 'legal_caselaw' đã được index chưa."

@tool
def find_related_caselaw(article_name: str, top_k: int=3) -> str:
    try:
        retriever = _get_caselaw_retriever()
        query = f'Bản án, quyết định áp dụng {article_name}'
        results = retriever.retrieve(query, top_k=top_k)
        if not results:
            return f"Không tìm thấy Án lệ nào từng áp dụng '{article_name}' trong dữ liệu hiện có."
        parts = [f'**CÁC ÁN LỆ / BẢN ÁN ĐÃ ÁP DỤNG {article_name.upper()}**:\n']
        for i, r in enumerate(results, 1):
            meta = r.get('metadata', {})
            title = meta.get('title') or meta.get('doc_name') or 'Bản án'
            detail_url = meta.get('detail_url', '')
            parts.append(f'[{i}] **{title}**')
            if detail_url:
                parts.append(f'    🔗 Nguồn: {detail_url}')
            parts.append(f"    {r.get('content', '')[:500].strip()}...")
            parts.append('')
        return '\n'.join(parts)
    except Exception as e:
        return f'Lỗi khi tìm án lệ liên quan: {str(e)}'

@tool
def search_legal_qa(query: str, top_k: int=5) -> str:
    try:
        retriever = _get_qa_retriever()
        results = retriever.retrieve(query, top_k=top_k)
        if not results:
            return 'Không tìm thấy câu hỏi đáp tương tự. Hãy dựa vào quy định pháp luật để tự phân tích.'
        parts = ['**KẾT QUẢ TRA CỨU HỎI ĐÁP PHÁP LUẬT**:\n']
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] **Tình huống**: {r.get('metadata', {}).get('question', 'Hỏi đáp')}")
            parts.append(f"    {r.get('content', '')[:1000].strip()}")
            parts.append('')
        return '\n'.join(parts)
    except Exception as e:
        return f'Lỗi khi tra cứu QA: {str(e)}'

@tool
def search_law_graph(article_name: str) -> str:
    db = get_graph_db()
    if not db.driver:
        return 'Tính năng GraphRAG chưa được cấu hình. Neo4j chưa chạy.'
    query = '\n    MATCH (t:Topic)-[:HAS_SUBJECT]->(s:Subject)-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_ARTICLE]->(a:Article)\n    WHERE a.title CONTAINS $article_name\n    RETURN t.name as topic, s.name as subject, c.name as chapter, a.title as article, a.content as content\n    LIMIT 3\n    '
    try:
        results = db.query(query, {'article_name': article_name})
        if not results:
            return f"Không tìm thấy mối liên hệ cho '{article_name}' trong Graph."
        parts = ['**KẾT QUẢ TỪ KNOWLEDGE GRAPH (Neo4j)**:\n']
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] **{r['topic']}** > **{r['subject']}** > **{r['chapter']}** > **{r['article']}**")
            parts.append(f"    {r['content'][:300]}...")
        return '\n'.join(parts)
    except Exception as e:
        return f'Lỗi truy vấn Graph: {str(e)}'

@tool
def search_web_for_latest_laws(query: str, max_results: int=3) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f'{query} quy định pháp luật việt nam', max_results=max_results))
        if not results:
            return 'Không tìm thấy thông tin trên mạng.'
        parts = ['**KẾT QUẢ TỪ WEB SEARCH**:\n']
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] **{r.get('title')}**")
            parts.append(f"    🔗 Nguồn: {r.get('href')}")
            parts.append(f"    {r.get('body')}")
            parts.append('')
        return '\n'.join(parts)
    except Exception as e:
        return f'Lỗi Web Search: {str(e)}'
legal_tools = [search_statutory_law, search_case_law, find_related_caselaw, search_legal_qa, search_law_graph, search_web_for_latest_laws]