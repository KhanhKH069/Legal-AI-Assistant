# Legal AI Assistant (Road to AI 2026) 🏆

Dự án Legal AI Assistant là một hệ thống Trí tuệ Nhân tạo chuyên biệt trong lĩnh vực Pháp lý (LegalTech), được xây dựng để tham gia cuộc thi **Road to AI 2026 — Truy hồi và Hỏi đáp Văn bản Pháp luật Tiếng Việt (SME)**.

Hệ thống được thiết kế dưới dạng **Multi-Agent** (nhiều AI tương tác với nhau) và ứng dụng kiến trúc **RAG (Retrieval-Augmented Generation) tiên tiến nhất**, giúp loại bỏ triệt để hiện tượng AI "bịa luật" (Hallucination) và mang lại câu trả lời chính xác từ Hệ thống Pháp điển Quốc gia và Án lệ Việt Nam.

> **Lưu ý Quy chế:** Hệ thống sử dụng **100% mô hình mã nguồn mở** (dưới 14B tham số, phát hành trước 01/03/2026), hoàn toàn tuân thủ Điều lệ của Ban Tổ chức.

---

## 🧠 MÔ HÌNH AI SỬ DỤNG

### LLM Chính (Bộ Não Hệ Thống)
| Model | Tham số | Phát hành | Vai trò |
|---|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct` | 7.6 Tỷ | Tháng 9/2024 | Sinh câu trả lời pháp lý, hỏi đáp |

> **Cách chạy:** Dùng [Ollama](https://ollama.com) để chạy LLM nội bộ. Chỉ cần mở Terminal và gõ: `ollama run qwen2.5`

### Các Model Phụ Trợ (Offline/HuggingFace)
Toàn bộ chạy 100% nội bộ, không cần API key bên ngoài.

| Model | Vai trò | Tham số |
|---|---|---|
| `truro7/vn-law-embedding` | Embedding vector (Chuyên pháp luật VN) | ~135M |
| `huynhdat543/VietNamese_law_rerank` | Reranker (Hybrid Search chính xác) | ~278M |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Semantic Cache (Tăng tốc) | ~118M |
| `Systran/faster-whisper-small` | Speech-to-Text (Nhận diện giọng nói) | ~244M |

---

## 🌟 TÍNH NĂNG NỔI BẬT (KILLER FEATURES)

1. **Thuật toán Hybrid Search + BGE Reranker:**
   Kết hợp Semantic Search (Vector) + Keyword Search (BM25) qua cơ chế RRF (Reciprocal Rank Fusion). Kết quả lọc lại bằng Cross-Encoder `VietNamese_law_rerank`, đảm bảo truy hồi 100% điều luật chính xác nhất.

2. **Dữ liệu SME Tập trung:**
   Chỉ nạp các bộ luật trực tiếp liên quan đến Doanh nghiệp vừa và nhỏ vào VectorDB. Loại bỏ toàn bộ nhiễu từ 60,000+ điều luật lĩnh vực khác (Hình sự, Hàng hải...).

3. **Thẩm định Rủi ro Hợp đồng (Contract Reviewing):**
   Upload file hợp đồng PDF, AI tự đọc, đối chiếu với Pháp điển và rà soát điều khoản vi phạm pháp luật.

4. **Luật 🤝 Án lệ Cross-Reference:**
   Khi tư vấn một Điều luật, AI tự động quét kho Án lệ để gợi ý Bản án thực tế đã áp dụng Điều luật đó.

5. **Dynamic Knowledge Graph (Đồ thị Tư duy Real-time):**
   Tự động sinh code Mermaid.js, render ngay thành Sơ đồ đồ thị SVG tương tác, giúp hiểu hệ thống phân cấp pháp luật (Luật → Nghị định → Thông tư).

6. **Script Nộp Bài Tự Động:**
   Script `scripts/generate_submission.py` tự động hóa toàn bộ quy trình từ câu hỏi → tra cứu → trả lời → xuất file `results.json` đúng format thi đấu.

---

## 🏗 KIẾN TRÚC HỆ THỐNG

- **Backend:** FastAPI (Python)
- **AI Orchestration:** LangGraph & LangChain
- **LLM Core:** `Qwen2.5-7B-Instruct` (qua Ollama, chuẩn OpenAI API)
- **Vector Database:** ChromaDB (lưu trữ local, không tốn phí cloud)
- **Keyword Index:** Rank-BM25
- **Frontend:** Next.js (React), TailwindCSS, React-Markdown, Mermaid.js
- **PDF Extraction:** PyMuPDF (fitz)

---

## 📂 CẤU TRÚC THƯ MỤC (PROJECT TREE)

```text
Legal-AI-Assistant/
├── api/                    # Backend API Server (FastAPI)
├── frontend/               # Giao diện người dùng (Next.js, React)
├── src/                    # Mã nguồn chính (AI Agents, Services, Tools)
│   ├── agents/             # Các LangGraph Agents (Statutory, Caselaw, Contract...)
│   ├── core/
│   │   ├── config.py       # Cấu hình hệ thống (LLM endpoint, model name...)
│   │   └── llm.py          # Factory function get_llm() — trung tâm khởi tạo LLM
│   ├── services/
│   │   ├── vector_db.py    # Quản lý ChromaDB
│   │   └── guardrail.py    # Bộ lọc chống bịa luật (Anti-Hallucination)
│   └── tools/              # Công cụ tra cứu pháp luật
├── scripts/
│   ├── download_datasets.py    # Tải Pháp điển + Án lệ từ HuggingFace
│   ├── index_sme_laws.py       # Lọc & Index 5 bộ luật SME vào ChromaDB
│   ├── generate_submission.py  # Tạo file results.json nộp thi 
│   └── index_legal_to_chromadb.py  # Index toàn bộ Pháp điển 
├── tests/                  # Unit & Integration tests
├── chroma_db/              # Lưu trữ Vector cục bộ (ChromaDB)
├── data/
│   └── raw/                # Dữ liệu nguồn Parquet (Pháp điển, Án lệ)
├── requirements.txt        # Danh sách thư viện Python
└── .env.example            # Mẫu cấu hình biến môi trường
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN

### Yêu cầu hệ thống
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/download) (để chạy Qwen2.5 nội bộ)
- RAM: 8GB+ | VRAM: 6GB+ (NVIDIA GPU)

### Bước 1: Cài đặt Ollama & tải LLM
```bash
# Cài Ollama (https://ollama.com/download), sau đó chạy:
ollama run qwen2.5
# Giữ cửa sổ này mở. Ollama sẽ serve LLM tại http://localhost:11434
```

### Bước 2: Cài đặt Backend Python
```bash
# Tạo môi trường ảo và cài đặt thư viện
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### Bước 3: Cấu hình biến môi trường
Tạo file `.env` từ mẫu:
```bash
copy .env.example .env
```
Mở `.env` và cấu hình (chỉ cần đổi nếu Ollama chạy ở cổng khác):
```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
LLM_MODEL_NAME=qwen2.5:7b
```

### Bước 4: Tải & Index Dữ liệu Pháp luật SME
```bash
# Tải bộ Pháp điển từ HuggingFace (~200MB)
python scripts/download_datasets.py

# Lọc và Index 5 bộ luật trọng tâm vào VectorDB (~3-5 phút)
python scripts/index_sme_laws.py
```

### Bước 5: Chạy Backend API
```bash
uvicorn api.main:app --reload
# API chạy tại: http://localhost:8000
```

### Bước 6: Chạy Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
# Giao diện web tại: http://localhost:3000
```

---

## 🏆 HƯỚNG DẪN NỘP BÀI THI (CUỘC THI ROAD TO AI 2026)

Khi Ban Tổ Chức phát file câu hỏi test (`test.json`):

```bash
# Bước 1: Sinh file kết quả (LLM cần đang chạy qua Ollama)
python scripts/generate_submission.py --input test.json --output results.json

# Bước 2: Nén thành file nộp bài
# Chuột phải vào results.json -> "Send to" -> "Compressed (zipped) folder"
# Đặt tên là: submission.zip

# Bước 3: Nộp file submission.zip lên Dashboard của BTC
```

> **Format output chuẩn BTC:** `<Mã văn bản>|<Tên văn bản>|<Điều>` (được đảm bảo bởi Pydantic Structured Output)

---

## 📚 DỮ LIỆU SỬ DỤNG

Hệ thống được Index riêng 5 bộ luật SME cốt lõi từ Pháp điển Quốc gia:

| # | Tên Bộ Luật | Số Hiệu |
|---|---|---|
| 1 | Luật Hỗ trợ Doanh nghiệp nhỏ và vừa | 04/2017/QH14 |
| 2 | Luật Doanh nghiệp | 59/2020/QH14 |
| 3 | Bộ luật Lao động | 45/2019/QH14 |
| 4 | Luật Thuế thu nhập doanh nghiệp | 14/2008/QH12 & sửa đổi |
| 5 | Luật Bảo hiểm xã hội | 58/2014/QH13 / 41/2024/QH15 |

**Nguồn dữ liệu mở (HuggingFace):**
- Pháp điển: `tmquan/phapdien-moj-gov-vn`
- Án lệ: `tmquan/anle-toaan-gov-vn`

*(Toàn bộ dữ liệu Raw được lưu trong `data/raw/` dưới dạng Parquet)*

---

**Tác giả:** Hệ thống được lập trình và tối ưu hóa 100% dành cho cuộc đua **Road to AI 2026**. Chúc đội thi gặt hái thành công lớn! 🏆
