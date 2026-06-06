# Legal AI Assistant (Road to AI 2026) 🏆

Hệ thống Trí tuệ Nhân tạo chuyên biệt trong lĩnh vực Pháp lý (LegalTech), được xây dựng để tham gia cuộc thi **Road to AI 2026 — Truy hồi và Hỏi đáp Văn bản Pháp luật Tiếng Việt (SME)**.

Hệ thống sử dụng kiến trúc **Multi-Agent** (LangGraph) kết hợp **GraphRAG** (ChromaDB + Neo4j) và thuật toán **Hybrid Search** (Vector + BM25 + Reranker), giúp loại bỏ triệt để hiện tượng AI "bịa luật" (Hallucination).

> **Lưu ý Quy chế:** Hệ thống sử dụng **100% mô hình mã nguồn mở** (dưới 14B tham số, phát hành trước 01/03/2026), hoàn toàn tuân thủ Điều lệ của Ban Tổ chức.

---

## 🧠 MÔ HÌNH AI SỬ DỤNG

### LLM Chính (Bộ Não Hệ Thống)

| Model | Tham số | Phát hành | Vai trò |
|---|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct` | 7.6 Tỷ | Tháng 9/2024 | Sinh câu trả lời pháp lý, hỏi đáp |

> **Cách chạy:** Dùng [Ollama](https://ollama.com) để chạy LLM nội bộ: `ollama run qwen2.5`

### Các Model Phụ Trợ (Offline/HuggingFace)

| Model | Vai trò | Tham số |
|---|---|---|
| `truro7/vn-law-embedding` | Embedding vector (Chuyên pháp luật VN) | ~135M |
| `huynhdat543/VietNamese_law_rerank` | Reranker (Hybrid Search chính xác) | ~278M |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Semantic Cache (Tăng tốc Redis) | ~118M |
| `Systran/faster-whisper-small` | Speech-to-Text (Nhận diện giọng nói) | ~244M |

---

## 🏗 KIẾN TRÚC HỆ THỐNG

```
Người dùng
    │
    ▼
FastAPI Backend (api/)
    │
    ▼
LangGraph Orchestrator
    ├── Statutory Agent  ──► ChromaDB (Pháp điển)
    ├── Caselaw Agent    ──► ChromaDB (Án lệ)
    ├── Reviewer Agent   ──► Kiểm tra chất lượng câu trả lời
    └── Contract Agent   ──► PyMuPDF + ChromaDB
         │
         ▼
    Neo4j (Knowledge Graph)  ◄──── GraphRAG queries
    Redis (Cache + Rate Limiter + Checkpointing)
```

**Stack công nghệ:**

| Layer | Công nghệ |
|---|---|
| Backend | FastAPI (Python) |
| AI Orchestration | LangGraph + LangChain |
| LLM Core | Qwen2.5-7B-Instruct (qua Ollama) |
| Vector Database | ChromaDB (local persistent) |
| Graph Database | Neo4j 5 Community |
| Keyword Search | Rank-BM25 (in-memory, index offline) |
| Caching | Redis (Semantic Cache + LLM Cache) |
| Frontend | Next.js, TailwindCSS, Mermaid.js |
| Task Queue | Celery + Redis |
| PDF Extraction | PyMuPDF (fitz) |
| Speech-to-Text | faster-whisper |

---

## 📂 CẤU TRÚC THƯ MỤC

```text
Legal-AI-Assistant/
├── api/                        # Backend API Server (FastAPI)
│   ├── main.py                 # App entry point, lifespan, middleware
│   ├── auth.py                 # JWT Authentication
│   ├── models.py               # SQLModel ORM models
│   ├── database.py             # SQLite/PostgreSQL engine
│   └── routers/
│       ├── chat.py             # Chat & Streaming SSE endpoints
│       ├── auth.py             # Login/Register endpoints
│       ├── audit.py            # Audit log endpoints
│       ├── document_review.py  # Contract review endpoints
│       └── stt.py              # Speech-to-Text endpoint
├── src/
│   ├── agents/                 # LangGraph Agents
│   │   ├── orchestrator.py     # Main agent graph + IntentRouting (Structured Output)
│   │   ├── guest_orchestrator.py   # Graph cho người dùng vãng lai
│   │   ├── statutory_agent.py  # Chuyên gia Pháp điển
│   │   ├── caselaw_agent.py    # Chuyên gia Án lệ
│   │   ├── reviewer_agent.py   # QA Reviewer (ReviewResult Structured Output)
│   │   └── contract_reviewer_agent.py  # Thẩm định hợp đồng
│   ├── core/
│   │   ├── config.py           # Cấu hình hệ thống (env vars, retrieval settings)
│   │   ├── llm.py              # Factory function get_llm()
│   │   ├── celery_app.py       # Celery task queue
│   │   ├── logging_config.py   # Logging setup
│   │   ├── prompt_loader.py    # Prompt template loader
│   │   ├── email_service.py    # Email notifications
│   │   └── storage.py          # File storage abstraction
│   ├── services/
│   │   ├── hybrid_retriever.py # Hybrid Search: Vector + BM25 + Reranker + RRF
│   │   ├── vector_db.py        # ChromaDB client wrapper
│   │   ├── graph_db.py         # Neo4j driver wrapper
│   │   ├── guardrail.py        # Anti-hallucination filter
│   │   └── metrics.py          # Request metrics collector
│   ├── tools/
│   │   └── legal_tools.py      # LangChain Tools (search_statutory_law, search_case_law...)
│   ├── tasks/
│   │   ├── async_review.py     # Async contract review Celery task
│   │   └── data_pipeline.py    # Data pipeline task
│   └── utils/
│       ├── helpers.py
│       └── logger.py
├── scripts/
│   ├── download_datasets.py        # Tải Pháp điển + Án lệ từ HuggingFace
│   ├── index_sme_laws.py           # Index 5 bộ luật SME vào ChromaDB
│   ├── index_legal_to_chromadb.py  # Index toàn bộ Pháp điển
│   ├── index_caselaw.py            # Index Án lệ
│   ├── index_to_neo4j.py           # Import dữ liệu vào Neo4j
│   ├── build_bm25_indices.py       # Build BM25 index offline
│   ├── ingest_qa.py                # Ingest dữ liệu QA
│   ├── generate_submission.py      # Tạo file results.json nộp thi
│   └── test_legal_search.py        # Kiểm tra chất lượng search
├── frontend/                   # Giao diện Next.js
├── alembic/                    # Database migrations
├── tests/                      # Unit & Integration tests
├── chroma_db/                  # Vector DB local storage
├── data/raw/                   # Dữ liệu Parquet (Pháp điển, Án lệ)
├── docker-compose.yml          # Dev: Backend + Frontend + Neo4j + Redis
├── docker-compose.prod.yml     # Production deployment
├── requirements.txt
└── .env                        # Biến môi trường
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN

### Yêu cầu hệ thống

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com/download)
- RAM: 8GB+ | VRAM: 6GB+ (NVIDIA GPU)
- Docker & Docker Compose (tùy chọn)

### Cách 1: Chạy thủ công (Local)

**Bước 1 — Khởi động LLM**
```bash
ollama run qwen2.5
```

**Bước 2 — Cài đặt Backend**
```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**Bước 3 — Cấu hình biến môi trường**

Tạo file `.env` với nội dung:
```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
LLM_MODEL_NAME=qwen2.5:7b
DATABASE_URL=sqlite:///data/sql_db/legal_agent.db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_secret_key_here
OFFLINE_MODE=false
```

**Bước 4 — Tải & Index dữ liệu** *(chỉ cần chạy 1 lần)*
```bash
python scripts/download_datasets.py
python scripts/index_sme_laws.py
python scripts/build_bm25_indices.py
python scripts/index_to_neo4j.py
```

**Bước 5 — Khởi tạo Database**
```bash
python scripts/init_db.py
```

**Bước 6 — Chạy Backend**
```bash
uvicorn api.main:app --reload --port 8000
```

**Bước 7 — Chạy Frontend**
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

### Cách 2: Chạy bằng Docker (khuyến nghị)

```bash
docker-compose up --build
```

---

## 🏆 HƯỚNG DẪN NỘP BÀI THI

Khi Ban Tổ Chức phát file câu hỏi test (`test.json`):

```bash
python scripts/generate_submission.py --input test.json --output results.json
```

Nén và nộp:
```bash
# Windows PowerShell
Compress-Archive -Path results.json -DestinationPath submission.zip -Force
```

> **Format output chuẩn BTC:** `<Mã văn bản>|<Tên văn bản>|<Điều>` (được đảm bảo bởi Pydantic Structured Output)

---

## 📚 DỮ LIỆU SỬ DỤNG

Hệ thống Index riêng 5 bộ luật SME cốt lõi từ Pháp điển Quốc gia:

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

---

## ⚙️ CẤU HÌNH NÂNG CAO

Các biến môi trường quan trọng:

| Biến | Mô tả | Mặc định |
|---|---|---|
| `LLM_MODEL_NAME` | Tên model Ollama | `qwen2.5:7b` |
| `OPENAI_API_BASE` | Ollama API endpoint | `http://localhost:11434/v1` |
| `BM25_RRF_K` | Hằng số k trong thuật toán RRF | `60` |
| `RETRIEVER_TOP_K` | Số kết quả trả về từ retriever | `5` |
| `TEMPERATURE` | Nhiệt độ sinh văn bản LLM | `0.0` |
| `MAX_TOKENS` | Số token tối đa mỗi response | `4000` |
| `OFFLINE_MODE` | Bỏ qua LLM (dùng cho testing) | `false` |
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

---
