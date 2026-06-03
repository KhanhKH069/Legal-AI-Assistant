import json
import argparse
import sys
from pathlib import Path
from tqdm import tqdm
from pydantic import BaseModel, Field

from src.core.llm import get_llm
from src.tools.legal_tools import search_statutory_law
from langchain_core.messages import HumanMessage, SystemMessage

class SubmissionResponse(BaseModel):
    answer: str = Field(description="Câu trả lời cho câu hỏi.")
    relevant_docs: list[str] = Field(description="Danh sách các văn bản pháp luật, ví dụ: ['04/2017/QH14|Luật Hỗ trợ doanh nghiệp nhỏ và vừa']")
    relevant_articles: list[str] = Field(description="Danh sách các điều luật, ví dụ: ['04/2017/QH14|Luật Hỗ trợ doanh nghiệp nhỏ và vừa|Điều 4']")

def generate_submission(input_file: str, output_file: str):
    print(f"Reading test data from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return

    llm = get_llm(temperature=0.0).with_structured_output(SubmissionResponse)

    system_prompt = """Bạn là một Luật sư xuất sắc, chuyên tư vấn pháp luật doanh nghiệp Việt Nam.
Nhiệm vụ của bạn là đọc các văn bản pháp luật được cung cấp (từ Pháp điển) và trả lời câu hỏi của người dùng.

YÊU CẦU QUAN TRỌNG VỀ ĐỊNH DẠNG ĐẦU RA (JSON BẮT BUỘC):
1. answer: Câu trả lời tự nhiên, chính xác, không bịa đặt.
2. relevant_docs: Mảng string. Dựa vào "Nguồn" trong văn bản, trích xuất chính xác "Mã văn bản" và "Tên văn bản". Format bắt buộc: `<Mã văn bản>|<Tên văn bản>`
Ví dụ: `"04/2017/QH14|Luật Hỗ trợ doanh nghiệp nhỏ và vừa"`
3. relevant_articles: Mảng string. Kèm theo Điều luật cụ thể. Format bắt buộc: `<Mã văn bản>|<Tên văn bản>|<Điều>`
Ví dụ: `"04/2017/QH14|Luật Hỗ trợ doanh nghiệp nhỏ và vừa|Điều 4"`

Hãy luôn kiểm tra kỹ phần "Nguồn" để lấy chính xác Mã và Tên văn bản.
Nếu "Nguồn" không có Mã văn bản, cố gắng suy luận từ tên văn bản hoặc trả về sát nhất.
"""

    results = []

    print("Starting evaluation loop...")
    for item in tqdm(data, desc="Evaluating"):
        question_id = item.get("id")
        question = item.get("question")

        context = search_statutory_law(question, top_k=5)

        prompt = f"Câu hỏi: {question}\n\nCăn cứ pháp luật tìm được:\n{context}"

        try:
            response: SubmissionResponse = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ])

            result_item = {
                "id": question_id,
                "question": question,
                "answer": response.answer,
                "relevant_docs": response.relevant_docs,
                "relevant_articles": response.relevant_articles
            }
        except Exception as e:
            print(f"Error processing question {question_id}: {e}")
            result_item = {
                "id": question_id,
                "question": question,
                "answer": "Hệ thống gặp lỗi trong quá trình xử lý.",
                "relevant_docs": [],
                "relevant_articles": []
            }

        results.append(result_item)

    print(f"Saving results to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Done! Please compress {output_file} into submission.zip to upload.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate submission for Legal QA Competition")
    parser.add_argument("--input", "-i", type=str, default="test.json", help="Path to test.json file")
    parser.add_argument("--output", "-o", type=str, default="results.json", help="Path to output results.json file")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Input file {args.input} does not exist. Please provide a valid test data file.")
        sys.exit(1)

    generate_submission(args.input, args.output)
