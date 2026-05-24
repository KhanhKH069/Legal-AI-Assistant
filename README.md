# Paraline HR AI Agent

Hệ thống **HR AI Assistant** đa tác nhân cho Paraline Vietnam — kiến trúc Microservices hiện đại: **Next.js 15 frontend**, **Python/FastAPI backend**, và **LangGraph orchestration**. Tích hợp **8 AI agents**, hỗ trợ **Dual-Mode Portal** (Nhân viên & Ứng viên), và **AI Performance Dashboard** thời gian thực.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js_15-Frontend-000000.svg)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-8--Agent-FF9900.svg)](https://python.langchain.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)](https://sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)

---

## 🏗️ Kiến Trúc Hệ Thống

```
Người dùng
│
├── 🟣 Guest / Ứng viên ──► localhost:3000/guest   (Không cần đăng nhập)
│                                  │
│                            Guest Chat UI ──► POST /chat/guest/stream
│                                  │                 │
│                            Guest Graph (giới hạn)  │
│                            └─ Recruitment Agent    │
│                               (screen CV, job info)│
│
└── 🟢 Nhân viên / Admin ──► localhost:3000         (Đăng nhập JWT)
                                   │
                            Employee HR Portal
                            ├─ Dashboard + Metrics
                            ├─ HR Assistant Chat ──► POST /chat/stream
                            │                              │
                            │                      Employee Graph (full)
                            │                      └─ 8 AI Agents
                            └─ Quản lý nhân sự
```

---

## 🔀 Dual-Mode Portal (Tính Năng Nổi Bật)

### 👤 Guest Portal — Cổng Ứng Viên (`/guest`)
- **Không cần đăng nhập** — ứng viên bấm vào và hỏi ngay
- Chỉ trả lời câu hỏi về: vị trí tuyển dụng, quy trình phỏng vấn, văn hóa công ty, phúc lợi tổng quan
- **Bảo mật tuyệt đối**: Guest Graph bị cắt đứt hoàn toàn khỏi database nhân sự → rủi ro Prompt Injection Data Leakage = **0%**
- Giao diện màu **tím** (Purple) thân thiện, gợi ý câu hỏi liên quan đến tuyển dụng

### 🏢 Employee Portal — Cổng Nội Bộ (`/dashboard`)
- Yêu cầu đăng nhập **JWT** với mã nhân viên
- Toàn quyền truy cập 8 AI Agents chuyên biệt
- Giao diện màu **xanh lá** (Emerald) chuyên nghiệp

---

## 🧠 Hệ Thống Multi-Agent (8 Agents)

```
User Message → FastAPI → Orchestrator (Gemini LLM classify intent)
                                │
    ┌──────┬──────┬──────┬──────┼──────┬──────┬──────┬──────┐
    ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
 POLICY ONBOARD  CV  ANALYTICS ATTEND HELP BENEFITS APPRAISE OFFLINE
```

| Agent | Chức năng |
|-------|-----------|
| **Policy Agent** | Giải đáp chính sách HR qua RAG (ChromaDB), tra cứu lương, tính thuế TNCN 7 bậc |
| **Onboard Agent** | Checklist onboarding, ký hợp đồng điện tử, cảnh báo hợp đồng hết hạn |
| **CV Agent** | Chấm điểm CV, Recruitment CRM Pipeline, lên lịch phỏng vấn |
| **Analytics Agent** | Chat với database HR bằng ngôn ngữ tự nhiên (Pandas) |
| **Attendance Agent** | Chấm công, OT, nộp đơn nghỉ phép với **Human-in-the-Loop** |
| **Helpdesk Agent** | Tạo và theo dõi HR Support Ticket |
| **Benefits Agent** | Gói bảo hiểm, phụ cấp, quyền lợi cá nhân |
| **Appraisal Agent** | Đánh giá hiệu suất, quản lý kỹ năng, Skill Gap Analysis |

---

## 📊 AI Performance Dashboard (Mới)

Trang **`/dashboard/metrics`** hiển thị real-time (auto-refresh mỗi 15 giây):

- **Tổng số request** (phân chia Nhân viên / Khách)
- **Cache Hit Rate** — bao nhiêu câu hỏi được trả lời từ bộ nhớ đệm
- **Thời gian phản hồi trung bình** theo từng Agent
- **Agent Usage Chart** — horizontal bar chart màu sắc từng agent
- **20 yêu cầu gần nhất** — timestamp, user, agent, câu hỏi preview, thời gian xử lý

---

## ⚡ Tối Ưu Hiệu Suất

### LangChain LLM Cache (SQLite)
Khi cùng một prompt được gửi lên LLM (bao gồm context RAG), hệ thống trả về ngay lập tức từ `data/llm_cache.db` mà **không cần gọi API Google**. Đặc biệt hiệu quả với Orchestrator routing.

### LangSmith Tracing (tuỳ chọn)
Thêm `LANGSMITH_API_KEY` vào `.env` để kích hoạt tracing toàn bộ AI pipeline lên LangSmith Dashboard. Giúp debug từng bước: Orchestrator → Agent → Tool → Response.

---

## 🔒 Bảo Mật & Xác Thực

- **JWT Authentication**: Bảo vệ toàn bộ Employee API với Bearer token
- **bcrypt Password Hashing**: Mật khẩu mã hóa an toàn trong SQLite
- **Role-Based Access Control (RBAC)**:
  - `admin/manager`: Toàn quyền, hiển thị nút Duyệt đơn trong chat
  - `employee`: Chỉ xem dữ liệu cá nhân, bị chặn HTTP 403 nếu vượt quyền
- **Guest Isolation**: Guest Graph độc lập hoàn toàn, không thể truy cập database nhân sự

**Tài khoản demo:**
- Admin: `EMP001` / `password123`
- Nhân viên: `EMP016` / `password123`
- Khách: Bấm "Tiếp tục với tư cách Khách" trên trang đăng nhập

---

## 🚀 Khởi Chạy (Docker — Khuyên dùng)

```bash
# 1 lệnh duy nhất — tự dựng Frontend + Backend + Database
docker-compose up --build -d
```

| Dịch vụ | URL |
|---------|-----|
| HR Portal (Nhân viên) | http://localhost:3000 |
| Guest Portal (Ứng viên) | http://localhost:3000/guest |
| API Documentation | http://localhost:8000/docs |
| AI Metrics (sau đăng nhập) | http://localhost:3000/dashboard/metrics |

### Cấu hình (`.env`)
```env
# Bắt buộc để chạy Online mode
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Tuỳ chọn — kích hoạt LangSmith Tracing
LANGSMITH_API_KEY=YOUR_LANGSMITH_API_KEY_HERE

# Tuỳ chọn — mặc định đã có giá trị
OFFLINE_MODE=false
MODEL_NAME=gemini-1.5-flash
JWT_SECRET_KEY=paraline_super_secret_key_2026
```

### Chạy thủ công (Developer mode)

**Backend:**
```bash
uv venv && .\.venv\Scripts\activate
uv pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install && npm run dev
```

---

## 🗂️ Cấu Trúc Dự Án

```
hr-ai-agent-pure-vector/
│
├── api/                          ← FastAPI Backend
│   ├── main.py                   ← App chính: Chat, Metrics, SSE Streaming
│   ├── auth.py                   ← JWT + bcrypt
│   ├── models.py                 ← SQLModel schemas
│   ├── database.py               ← SQLite connection
│   └── routers/                  ← 16 API routers (employees, attendance, ...)
│
├── src/
│   ├── agents/                   ← 8 AI Agents + Orchestrator + Guest Graph
│   │   └── orchestrator.py       ← Employee Graph + Guest Graph (tách biệt)
│   ├── services/
│   │   ├── metrics.py            ← AI Performance Metrics Collector (Mới)
│   │   ├── hybrid_retriever.py   ← Vector + BM25 Hybrid Search
│   │   └── vector_db.py          ← ChromaDB + Multilingual Embeddings
│   └── tools/                    ← 15+ tool modules (policy, attendance, ...)
│
├── config/
│   └── prompts.yaml              ← System prompts cho tất cả agents (+ guest)
│
├── frontend/                     ← Next.js 15 App Router
│   └── src/app/
│       ├── page.tsx              ← Trang Login (có nút Guest)
│       ├── guest/                ← Guest Portal (màu tím, không cần auth)
│       └── dashboard/
│           ├── chat/             ← Employee HR Chat
│           ├── employees/        ← Quản lý nhân sự
│           ├── profile/          ← Hồ sơ cá nhân
│           └── metrics/          ← AI Performance Dashboard (Mới)
│
├── documents/                    ← Tài liệu HR (Markdown) cho RAG
├── data/                         ← SQLite DBs: paraline.db, llm_cache.db
├── chroma_db/                    ← Vector store (persist)
├── docker/
│   └── Dockerfile.backend        ← Python/FastAPI Docker image
├── docker-compose.yml            ← Orchestrate toàn bộ hệ thống
└── requirements.txt
```

---

## 🌟 Tính Năng Nổi Bật

| Tính năng | Mô tả |
|-----------|-------|
| **Dual-Mode Portal** | Guest (ứng viên) và Employee (nội bộ) dùng UI riêng, Agent riêng, bảo mật riêng |
| **AI Streaming** | Server-Sent Events (SSE) — response "nhả chữ" realtime như ChatGPT |
| **Human-in-the-Loop** | Dừng lại chờ Manager bấm "Duyệt" trước khi thực hiện thao tác nhạy cảm |
| **Multilingual RAG** | Embedding Tiếng Việt chính xác với `paraphrase-multilingual-MiniLM-L12-v2` |
| **LLM Cache** | SQLite-backed cache — câu hỏi trùng trả về ngay, tiết kiệm API cost |
| **AI Metrics Dashboard** | Real-time monitoring: agent usage, response time, cache hit rate |
| **LangSmith Tracing** | Debug AI pipeline chi tiết từng bước (opt-in qua API key) |
| **Offline Fallback** | Tự động chuyển về KB nội bộ khi mất mạng hoặc thiếu API key |
| **RBAC** | Phân quyền cấp API: Admin / Manager / Employee / Guest |

---

## 📄 License

MIT License — Mã nguồn mở, tự do sử dụng và tùy chỉnh.

**Paraline Software • Japan Quality in Vietnam 🇯🇵🇻🇳**
