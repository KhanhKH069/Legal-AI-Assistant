# Legal AI Assistant (Road to AI 2026) 🏆

Dự án Legal AI Assistant là một hệ thống Trí tuệ Nhân tạo chuyên biệt trong lĩnh vực Pháp lý (LegalTech), được xây dựng để tham gia cuộc thi **Road to AI 2026**.

Hệ thống được thiết kế dưới dạng **Multi-Agent** (nhiều AI tương tác với nhau) và ứng dụng kiến trúc **RAG (Retrieval-Augmented Generation) tiên tiến nhất**, giúp loại bỏ triệt để hiện tượng AI "bịa luật" (Hallucination) và mang lại câu trả lời với độ chính xác tuyệt đối từ Hệ thống Pháp điển Quốc gia và Án lệ Việt Nam.

---

## 🌟 TÍNH NĂNG NỔI BẬT (KILLER FEATURES)

1. **Thuật toán Hybrid Search + BGE Reranker:**
   Sự kết hợp hoàn hảo giữa Semantic Search (Vector) và Keyword Search (BM25) qua cơ chế RRF (Reciprocal Rank Fusion). Kết quả sau đó được lọc lại bằng mô hình Cross-Encoder `BAAI/bge-reranker-v2-m3` tối ưu riêng cho Tiếng Việt, đảm bảo AI bốc trúng 100% điều luật chính xác nhất.

2. **Thẩm định Rủi ro Hợp đồng (Contract Reviewing):**
   Người dùng có thể upload một file hợp đồng PDF. AI sẽ tự động đọc, bóc tách từng điều khoản, và đối chiếu với quy định trong Pháp điển để rà soát các điều khoản vi phạm pháp luật hoặc có rủi ro pháp lý.

3. **Luật 🤝 Án lệ Cross-Reference:**
   Tính năng đọc chéo tự động. Khi tư vấn một Điều luật, AI sẽ tự động quét chéo kho Án lệ để gợi ý các Bản án thực tế đã từng áp dụng Điều luật đó.

4. **Dynamic Knowledge Graph (Đồ thị Tư duy Real-time):**
   Mỗi khi tư vấn các bộ luật phức tạp (Luật -> Nghị định -> Thông tư), AI sẽ tự động sinh code Mermaid.js để giao diện Frontend render ngay lập tức thành một **Sơ đồ đồ thị SVG tương tác**, giúp người dùng hiểu rõ hệ thống phân cấp pháp luật chỉ trong 1 giây.

5. **Giao diện Legal UI Đẳng cấp:**
   Xây dựng bằng Next.js, Tailwind CSS với phong cách Dark Mode, Glassmorphism sang trọng. Mọi trích dẫn luật đều biến thành các "Glowing Buttons" (nút bấm phát sáng) có thể click để đọc nguồn gốc.

---

## 🏗 KIẾN TRÚC HỆ THỐNG

- **Backend:** FastAPI (Python)
- **AI Orchestration:** LangGraph & LangChain
- **LLM Core:** Google Gemini 1.5 Pro
- **Vector Database:** ChromaDB (Lưu trữ Vector dưới local, không tốn phí cloud)
- **Keyword Index:** Rank-BM25
- **Frontend:** Next.js (React), TailwindCSS, React-Markdown, Mermaid.js
- **PDF Extraction:** PyMuPDF (fitz)

---

## 📂 CẤU TRÚC THƯ MỤC (PROJECT TREE)

```text
hr-ai-agent-pure-vector/
├── api/                # Backend API Server (FastAPI)
├── frontend/           # Giao diện người dùng (Next.js, React)
├── dashboard/          # Trang quản trị / Dashboard
├── src/                # Mã nguồn chính (AI Agents, Services, Tools)
├── tests/              # Unit & Integration tests
├── config/             # Cấu hình dự án
├── alembic/            # Scripts migrate cho Database
├── chroma_db/          # Lưu trữ dữ liệu Vector cục bộ (ChromaDB)
├── data/               # Dữ liệu nguồn (Pháp điển, Án lệ)
├── docker/             # Các cấu hình Docker
├── docs/               # Tài liệu dự án
├── k8s/                # Cấu hình Kubernetes để deploy
├── scripts/            # Các scripts tiện ích
├── Dockerfile          # Cấu hình build Docker image
├── docker-compose.yml  # Triển khai hệ thống qua Docker Compose
└── requirements.txt    # Danh sách các thư viện Python
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & CHẠY DỰ ÁN

### Yêu cầu hệ thống
- Python 3.10+
- Node.js 18+
- Biến môi trường: Bạn cần có `GOOGLE_API_KEY` (Gemini API) trong file `.env`.

### 1. Cài đặt Backend
Mở Terminal 1 và chạy các lệnh sau:
```bash
# Cài đặt thư viện Python
pip install -r requirements.txt

# Khởi động Backend API (Chạy ở cổng 8000)
uvicorn api.main:app --reload
```

### 2. Cài đặt Frontend
Mở Terminal 2, di chuyển vào thư mục `frontend` và chạy:
```bash
cd frontend

# Cài đặt thư viện Node (Bao gồm react-markdown, mermaid)
npm install --legacy-peer-deps

# Khởi động Giao diện Web (Chạy ở cổng 3000)
npm run dev
```

### 3. Trải nghiệm
Mở trình duyệt và truy cập: **http://localhost:3000**

---

## 📚 DỮ LIỆU SỬ DỤNG
Dự án sử dụng bộ dữ liệu mã nguồn mở được xử lý từ các hệ thống văn bản pháp luật chính thức của Việt Nam:
1. **Pháp điển:** Dữ liệu từ `phapdien.moj.gov.vn`
2. **Án lệ & Bản án:** Dữ liệu từ `anle.toaan.gov.vn`

*(Toàn bộ dữ liệu Raw được lưu trữ trong thư mục `data/raw`)*

---
**Tác giả:** Hệ thống được lập trình và tối ưu hóa 100% dành cho cuộc đua **Road to AI 2026**. Chúc đội thi gặt hái thành công lớn! 🏆
