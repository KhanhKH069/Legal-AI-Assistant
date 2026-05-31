# Paraline HR AI Agent (Enterprise Edition)

Hệ thống **HR AI Assistant** đa tác nhân chuẩn Enterprise cho Paraline Vietnam. Kiến trúc Microservices hiện đại kết hợp **Next.js 15 Frontend**, **FastAPI Backend**, **Celery + Redis Background Workers**, và **LangGraph Orchestration**. Được trang bị khả năng triển khai lên **Kubernetes (K8s)** với Auto-scale vô hạn.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js_15-Frontend-000000.svg)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-8_Agents-FF9900.svg)](https://python.langchain.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K8s-326CE5.svg)](https://kubernetes.io/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-101_Tests_Passing-success.svg)](https://github.com/KhanhKH069/hr-ai-agent/actions)

---

## 🏗️ Kiến Trúc Hệ Thống (Microservices)

```
Người dùng
│
├── 🟣 Khách / Ứng viên ──► Cổng thông tin (Port 3000)
│   (Upload CV PDF / Thẻ cư trú JPG)
│
└── 🟢 Nhân sự / Admin ──► Dashboard & Chatbot (Port 3000)
             │
             ▼
     [ API GATEWAY (FastAPI - Port 8000) ] ◄──► [ REDIS (Message Broker & Cache) ]
             │                                              │
      (LangGraph Routing)                                   ▼
             │                                    [ CELERY WORKER ]
    ┌────────┴────────┐                           (Xử lý tải nặng ngầm)
    ▼                 ▼                           - OCR Trích xuất chữ từ Ảnh
[8 AI Agents]   [Hybrid Search]                   - Vẽ & Render CV ra file PDF
                (Vector + BM25)
                      │
                [Flashrank Re-ranker]
                (Xếp hạng siêu tốc trên CPU)
```

---

## 🚀 Các Bản Cập Nhật Mới Nhất (Enterprise-Ready)

1. **RAG Re-ranking Layer (Flashrank)**: Tích hợp thư viện `flashrank` (chạy độc lập 100% Offline trên CPU, siêu nhẹ ~30MB). Tăng độ chính xác khi truy xuất chính sách HR lên mức tối đa mà không tốn RAM.
2. **Kubernetes (K8s) Orchestration**: Tích hợp sẵn 7 file YAML chuẩn quốc tế (`k8s/`). Hệ thống được cài đặt **HPA (Horizontal Pod Autoscaler)** — tự động "phân thân" Celery Worker (từ 2 lên 10 pods) khi đợt tuyển dụng có hàng vạn ứng viên nộp CV, và tự thu gọn khi vắng khách.
3. **CI/CD Pipeline Tự Động**: Cấu hình GitHub Actions chạy toàn bộ **101 Unit Tests** chặn đứng lỗi trước khi merge code vào nhánh chính.
4. **Standalone BI Dashboard (Streamlit)**: Giao diện chỉ huy dành riêng cho Giám đốc nhân sự theo dõi thời gian thực (Realtime) tốc độ phản hồi của AI, lưu lượng tải, biểu đồ phân bổ tác vụ.
5. **100% Offline Mode Readiness**: OCR thẻ cư trú, trích xuất dữ liệu, render PDF, phân tích RAG đều chạy ngầm cục bộ mà không để lọt một byte dữ liệu nào ra ngoài mạng Internet.

---

## 🔀 Tính Năng Cốt Lõi

### 1. Dual-Mode Portal
- **Guest Portal (Ứng viên)**: Giao diện thân thiện, không cần đăng nhập. Ứng viên có thể hỏi đáp về quy trình phỏng vấn hoặc **Upload CV (PDF) & Thẻ cư trú (Ảnh JPG/PNG)**. Agent sẽ tự động bóc tách (OCR), chấm điểm và lưu vào Pipeline.
- **Employee Portal (Nội bộ)**: Yêu cầu đăng nhập JWT. Nhân viên có thể tạo đơn xin nghỉ phép, tra cứu lương, chấm công (tích hợp **Human-in-the-Loop** chờ Manager duyệt).

### 2. Hệ Thống Multi-Agent (8 Chuyên Gia AI)
- **Policy Agent**: Trả lời chính sách, tính thuế TNCN.
- **Onboard Agent**: Checklist nhận việc, ký hợp đồng.
- **CV Agent**: Đọc CV, OCR thẻ cư trú, chấm điểm, lên lịch phỏng vấn.
- **Analytics Agent**: Chat với Data SQL bằng ngôn ngữ tự nhiên.
- **Attendance Agent**, **Helpdesk Agent**, **Benefits Agent**, **Appraisal Agent**...

---

## ⚡ Hướng Dẫn Chạy & Triển Khai

### 1. Chạy Demo Nhanh (Local Development)
Dành cho mục đích test nhanh, phát triển hoặc chạy demo nhỏ trên máy cá nhân. Không cần thiết lập Docker hay Kubernetes.

**Terminal 1: Chạy Backend (FastAPI)**
```bash
# Cài đặt thư viện Python (nếu cần)
pip install -r requirements.txt

# Chạy server FastAPI bằng Uvicorn
uvicorn api.main:app --reload
```
*API Docs (Swagger UI): `http://localhost:8000/docs`*

**Terminal 2: Chạy Frontend (Next.js)**
```bash
cd frontend
npm install
npm run dev
```
*Truy cập Giao diện Web: `http://localhost:3000`*

### 2. Triển Khai Toàn Diện (Docker Compose)
Dựng toàn bộ hệ sinh thái (Next.js, FastAPI, Celery, Redis, Streamlit BI Dashboard) bằng 1 lệnh:

```bash
docker-compose up --build -d
```

| Dịch vụ | Địa chỉ truy cập |
|---------|-----------------|
| **Cổng HR & Khách** | `http://localhost:3000` |
| **Admin BI Dashboard** | `http://localhost:8501` |
| **Backend API Docs** | `http://localhost:8000/docs` |

### 3. Triển Khai Lên Kubernetes (K8s Cloud)
Dành cho môi trường Production quy mô lớn (AWS EKS, GKE, Azure AKS):
```bash
kubectl apply -f k8s/
```

---

## 🔒 Bảo Mật & Xác Thực

- **Bảo vệ toàn diện**: JWT Bearer Tokens, Mã hóa bcrypt, Phân quyền RBAC (Admin, Manager, Employee, Guest).
- **Guest Isolation**: Ứng viên (Guest) chạy trên một LangGraph hoàn toàn tách biệt, chặn đứng rủi ro Prompt Injection đánh cắp dữ liệu lương nội bộ.

**Tài khoản Demo Local:**
- Admin: `EMP001` / `password123`
- Nhân viên: `EMP016` / `password123`

---

## 🗂️ Cấu Trúc Dự Án (Monorepo)

```
hr-ai-agent-pure-vector/
│
├── api/                  ← FastAPI Endpoints & RBAC Auth
├── src/
│   ├── agents/           ← 8 LangGraph AI Agents
│   ├── services/         ← Flashrank RAG, Metrics, VectorDB
│   ├── core/             ← Celery App, Configs
│   └── tools/            ← OCR, PDF Generation, Tools
│
├── frontend/             ← Next.js 15 UI (React)
├── dashboard/            ← Streamlit BI Admin Dashboard
├── k8s/                  ← Kubernetes YAML Manifests
├── documents/            ← Tài liệu Markdown gốc cho AI đọc
├── data/                 ← SQL Database, Logs
│
├── docker-compose.yml    ← Liên kết Frontend + Backend + Redis + Celery + Dashboard
├── Dockerfile            ← Backend / Worker Image
└── pytest.ini            ← Cấu hình Unit Tests (101/101 Passed)
```

---

**Paraline Software • Japan Quality in Vietnam 🇯🇵🇻🇳**
