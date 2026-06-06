import json
import argparse
import logging
import sys
from pathlib import Path
from tqdm import tqdm

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    _HAS_TENACITY = True
except ImportError:
    _HAS_TENACITY = False

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.llm import get_llm
from src.services.hybrid_retriever import get_hybrid_retriever
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = '''Bạn là một Luật sư xuất sắc, chuyên tư vấn pháp luật doanh nghiệp Việt Nam.
Nhiệm vụ của bạn là đọc các văn bản pháp luật được cung cấp và viết câu trả lời ngắn gọn, chính xác cho câu hỏi.
Chỉ trả lời dựa trên các văn bản đã được cung cấp. Không bịa đặt. Không cần trích dẫn số điều trong câu trả lời.'''


def build_citations_from_metadata(results: list) -> tuple[list[str], list[str]]:
    """
    Deterministically build relevant_docs and relevant_articles from
    the pre-parsed metadata fields (doc_code, doc_name, real_article)
    stored in ChromaDB. No LLM hallucination possible.
    """
    seen_docs = {}
    seen_articles = {}

    for r in results:
        meta = r.get('metadata', {})
        doc_code = (meta.get('doc_code') or '').strip()
        doc_name = (meta.get('doc_name') or '').strip()
        real_article = (meta.get('real_article') or '').strip()

        if not doc_code:
            continue

        if doc_code not in seen_docs:
            seen_docs[doc_code] = doc_name
        elif not seen_docs[doc_code] and doc_name:
            seen_docs[doc_code] = doc_name

        if real_article:
            key = (doc_code, real_article)
            seen_articles[key] = True

    relevant_docs = []
    for code, name in seen_docs.items():
        if name:
            relevant_docs.append(f'{code}|{name}')
        else:
            relevant_docs.append(code)

    relevant_articles = []
    for (code, article) in seen_articles:
        name = seen_docs.get(code, '')
        if name:
            relevant_articles.append(f'{code}|{name}|{article}')
        else:
            relevant_articles.append(f'{code}|{article}')

    return relevant_docs, relevant_articles


def get_context_text(results: list) -> str:
    """Format retrieval results into a readable text block for LLM."""
    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get('metadata', {})
        content = r.get('content', '')
        article_title = meta.get('article_title', '')
        source_note = meta.get('source_note', '')
        parts.append(f'[{i}] {article_title}')
        if source_note:
            parts.append(f'    Nguồn: {source_note}')
        parts.append(f'    {content[:600].strip()}')
        parts.append('')
    return '\n'.join(parts)


def _invoke_with_retry(llm, messages, max_attempts: int = 3):
    """Invoke LLM with retry on failure."""
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return llm.invoke(messages)
        except Exception as e:
            last_err = e
            logger.warning('[LLM] Attempt %d/%d failed: %s', attempt, max_attempts, e)
    raise RuntimeError(f'LLM failed after {max_attempts} attempts') from last_err


def _retrieve_with_retry(retriever, question: str, top_k: int = 5, max_attempts: int = 3):
    """Retrieve with retry on failure."""
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return retriever.retrieve(question, top_k=top_k)
        except Exception as e:
            last_err = e
            logger.warning('[Retriever] Attempt %d/%d failed: %s', attempt, max_attempts, e)
    logger.error('[Retriever] All %d attempts failed: %s', max_attempts, last_err)
    return []


def generate_submission(input_file: str, output_file: str):
    print(f'Reading test data from {input_file}...')
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'Error loading {input_file}: {e}')
        return

    llm = get_llm(temperature=0.0)
    retriever = get_hybrid_retriever('legal_statutory')

    results = []
    processed_ids = set()
    if Path(output_file).exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                processed_ids = {item['id'] for item in results}
            print(f'Resuming from {len(results)} previously processed items.')
        except Exception as e:
            print(f'Could not load existing {output_file}: {e}')

    print('Starting evaluation loop...')
    data_to_process = [item for item in data if item.get('id') not in processed_ids]

    for item in tqdm(data_to_process, desc='Evaluating'):
        question_id = item.get('id')
        question = item.get('question')

        retrieved = _retrieve_with_retry(retriever, question, top_k=5)

        relevant_docs, relevant_articles = build_citations_from_metadata(retrieved)
        context_text = get_context_text(retrieved)
        prompt = f'Câu hỏi: {question}\n\nCăn cứ pháp luật:\n{context_text}'
        try:
            response = _invoke_with_retry(llm, [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt)
            ])
            answer = response.content.strip()
        except Exception as e:
            logger.error('[Q%s] LLM failed after all retries: %s', question_id, e)
            answer = 'Hệ thống gặp lỗi trong quá trình xử lý.'

        result_item = {
            'id': question_id,
            'question': question,
            'answer': answer,
            'relevant_docs': relevant_docs,
            'relevant_articles': relevant_articles,
        }
        results.append(result_item)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

    print(f'\nDone! {len(results)} questions processed.')
    print(f'Output: {output_file}')
    print('Next: Compress-Archive -Path results.json -DestinationPath submission.zip -Force')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate submission for Legal QA Competition')
    parser.add_argument('--input', '-i', type=str, default='data/raw/R2AIStage1DATA.json',
                        help='Path to input test data JSON file')
    parser.add_argument('--output', '-o', type=str, default='results.json',
                        help='Path to output results.json file')
    args = parser.parse_args()
    if not Path(args.input).exists():
        print(f'Input file {args.input} does not exist. Please provide a valid test data file.')
        sys.exit(1)
    generate_submission(args.input, args.output)