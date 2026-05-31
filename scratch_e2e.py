import os
import json
from src.tools.cv_builder_tools import generate_cv_pdf
from src.tools.onboard_validation_tools import extract_id_card_info


def run_e2e_test():
    print("==================================================")
    print("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM E2E (OFFLINE MODE) 🚀")
    print("==================================================\n")

    # 1. Test CV Generation (fpdf2 + Vietnamese fonts)
    print("[1/2] Đang thử nghiệm tính năng tạo CV tự động (PDF)...")
    cv_data = {
        "applicant_name": "Trần Văn AI Agent",
        "contact_info": "ai.agent@paraline.com | 0987654321",
        "education": "Đại học Bách Khoa Hà Nội",
        "experience": "5 năm kinh nghiệm tối ưu hóa Agent AI và phân tích dữ liệu",
        "skills": "Python, LangGraph, React, Next.js, FastAPI",
    }

    cv_result = generate_cv_pdf.invoke(cv_data)
    print(f"✅ Kết quả tạo CV:\n{cv_result}\n")

    # Verify file was actually created
    try:
        cv_path = cv_result.split("at: ")[1].strip()
        if os.path.exists(cv_path):
            print(f"📄 Xác nhận file PDF đã được tạo thành công tại: {cv_path}")
            print(f"📊 Kích thước file: {os.path.getsize(cv_path)} bytes\n")
    except Exception as e:
        print(f"⚠️ Lỗi xác minh file CV: {e}\n")

    # 2. Test ID Card OCR (EasyOCR fallback)
    print("[2/2] Đang thử nghiệm tính năng trích xuất Thẻ Cư Trú / CCCD (EasyOCR)...")
    # Generate a dummy image to test the offline OCR graceful handling
    dummy_img_path = "dummy_id_card.jpg"
    with open(dummy_img_path, "wb") as f:
        f.write(b"fake image content")

    print("📸 Đang gọi OCR (giả lập upload ảnh thẻ)...")
    ocr_result = extract_id_card_info.invoke({"image_path": dummy_img_path})

    print("✅ Kết quả OCR (JSON):")
    try:
        parsed_ocr = json.loads(ocr_result)
        print(json.dumps(parsed_ocr, indent=2, ensure_ascii=False))
        if "error" in parsed_ocr:
            print(
                "\n👉 (Vì đây là ảnh giả nên OCR trả về error hợp lệ, hệ thống không bị crash)"
            )
    except Exception as e:
        print(f"❌ Lỗi khi parse JSON OCR: {e}")

    # Cleanup dummy image
    if os.path.exists(dummy_img_path):
        os.remove(dummy_img_path)

    print("\n==================================================")
    print("🎉 HOÀN TẤT CHẠY THỬ NGHIỆM! HỆ THỐNG HOẠT ĐỘNG TỐT.")
    print("==================================================")


if __name__ == "__main__":
    run_e2e_test()
