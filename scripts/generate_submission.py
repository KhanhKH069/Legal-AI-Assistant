import json
import argparse
import logging
import re
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ── How many documents to retrieve per question ───────────────────────────────
TOP_K = 10  # was 5 — increasing recall significantly

# ── Fallback regex for documents indexed without doc_code metadata ────────────
_DOC_CODE_RE = re.compile(
    r'\b(\d{1,3}/\d{4}/'
    r'(?:QH\d+|NĐ-CP|TT-[A-ZĐBCTN]+(?:-[A-ZĐBCTN]+)*'
    r'|TTLT-[A-ZĐBCTN]+(?:[-A-ZĐBCTN]+)*'
    r'|CT-TTg|QĐ-TTg|UBTVQH\d+))\b'
)


def _fallback_parse_doc_code(source_note: str):
    """
    Fallback: parse doc_code + doc_name directly from source_note text.
    Used for documents that were indexed before the metadata fix.
    """
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


def _fallback_parse_real_article(article_title: str) -> str:
    """
    Fallback: extract real article number from phapdien internal code.
    "Điều 5.1.NĐ.2.7. Điều kiện..." → "Điều 7"
    """
    code_m = re.match(r'Điều\s+([\d.A-ZĐNQTL]+?)\.\s', article_title)
    if code_m:
        nums = re.findall(r'\d+', code_m.group(1))
        if nums:
            return f'Điều {nums[-1]}'
    fallback = re.search(r'Điều\s+(\d+)', article_title)
    return f'Điều {fallback.group(1)}' if fallback else ''


SYSTEM_PROMPT = (
    'Bạn là một Luật sư xuất sắc, chuyên tư vấn pháp luật doanh nghiệp Việt Nam.\n'
    'Nhiệm vụ của bạn là đọc các văn bản pháp luật được cung cấp và viết câu trả lời '
    'ngắn gọn, chính xác cho câu hỏi.\n'
    'Chỉ trả lời dựa trên các văn bản đã được cung cấp. Không bịa đặt. '
    'Không cần trích dẫn số điều trong câu trả lời.'
)


def build_citations_from_metadata(results: list) -> tuple[list[str], list[str]]:
    """
    Build relevant_docs and relevant_articles from retrieval results.

    Priority order for doc_code/doc_name:
      1. Pre-parsed metadata fields (doc_code, doc_name, real_article) — fast, exact
      2. Fallback: parse from source_note text — for legacy-indexed documents
    """
    seen_docs: dict[str, str] = {}    # doc_code → doc_name
    seen_articles: dict[tuple, bool] = {}  # (doc_code, real_article) → True

    for r in results:
        meta = r.get('metadata', {})

        doc_code     = (meta.get('doc_code') or '').strip()
        doc_name     = (meta.get('doc_name') or '').strip()
        real_article = (meta.get('real_article') or '').strip()

        # ── Fallback: parse from source_note if metadata fields are missing ───
        if not doc_code:
            source_note = (meta.get('source_note') or '').strip()
            doc_code, doc_name = _fallback_parse_doc_code(source_note)

        if not doc_code:
            continue

        # ── Fallback: parse real_article from article_title ───────────────────
        if not real_article:
            article_title = (meta.get('article_title') or '').strip()
            real_article = _fallback_parse_real_article(article_title)

        # ── Accumulate ────────────────────────────────────────────────────────
        if doc_code not in seen_docs:
            seen_docs[doc_code] = doc_name
        elif not seen_docs[doc_code] and doc_name:
            seen_docs[doc_code] = doc_name  # upgrade empty name

        if real_article:
            seen_articles[(doc_code, real_article)] = True

    relevant_docs = [
        f'{code}|{name}' if name else code
        for code, name in seen_docs.items()
    ]
    relevant_articles = [
        f'{code}|{seen_docs.get(code, "")}|{article}' if seen_docs.get(code) else f'{code}|{article}'
        for code, article in seen_articles
    ]
    return relevant_docs, relevant_articles


def get_context_text(results: list) -> str:
    """Format retrieval results into a readable text block for LLM."""
    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get('metadata', {})
        content = r.get('content', '')
        # Use real article info when available
        doc_code     = meta.get('doc_code', '')
        doc_name     = meta.get('doc_name', '')
        real_article = meta.get('real_article', '')
        article_title = meta.get('article_title', '')
        source_note  = meta.get('source_note', '')

        if doc_code and real_article:
            header = f'{real_article} — {doc_name or doc_code}'
        elif article_title:
            header = article_title
        else:
            header = f'Kết quả {i}'

        parts.append(f'[{i}] {header}')
        if source_note and not doc_code:  # only show raw note if parsed fields unavailable
            parts.append(f'    Nguồn: {source_note[:150]}')
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


def _retrieve_with_retry(retriever, question: str, top_k: int = TOP_K, max_attempts: int = 3):
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
    processed_ids: set = set()
    if Path(output_file).exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                processed_ids = {item['id'] for item in results}
            print(f'Resuming from {len(results)} previously processed items.')
        except Exception as e:
            print(f'Could not load existing {output_file}: {e}')

    data_to_process = [item for item in data if item.get('id') not in processed_ids]
    print(f'Processing {len(data_to_process)} questions with top_k={TOP_K}...')

    for item in tqdm(data_to_process, desc='Evaluating'):
        question_id = item.get('id')
        question    = item.get('question')

        retrieved = _retrieve_with_retry(retriever, question, top_k=TOP_K)

        relevant_docs, relevant_articles = build_citations_from_metadata(retrieved)
        context_text = get_context_text(retrieved)
        prompt = f'Câu hỏi: {question}\n\nCăn cứ pháp luật:\n{context_text}'

        try:
            response = _invoke_with_retry(llm, [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            answer = response.content.strip()
        except Exception as e:
            logger.error('[Q%s] LLM failed after all retries: %s', question_id, e)
            answer = 'Hệ thống gặp lỗi trong quá trình xử lý.'

        result_item = {
            'id':               question_id,
            'question':         question,
            'answer':           answer,
            'relevant_docs':    relevant_docs,
            'relevant_articles': relevant_articles,
        }
        results.append(result_item)

        # Write after every question for crash-safety
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

    print(f'\nDone! {len(results)} questions processed → {output_file}')
    print('Next step: Compress-Archive -Path results.json -DestinationPath submission.zip -Force')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate submission for Legal QA Competition')
    parser.add_argument('--input',  '-i', type=str,
                        default='data/raw/R2AIStage1DATA.json',
                        help='Path to input test data JSON file')
    parser.add_argument('--output', '-o', type=str,
                        default='results.json',
                        help='Path to output results.json file')
    parser.add_argument('--top-k', '-k', type=int,
                        default=TOP_K,
                        help='Number of documents to retrieve per question')
    args = parser.parse_args()

    if args.top_k != TOP_K:
        TOP_K = args.top_k
        logger.info('top_k overridden to %d via CLI', TOP_K)

    if not Path(args.input).exists():
        print(f'Input file {args.input} does not exist.')
        sys.exit(1)

    generate_submission(args.input, args.output)