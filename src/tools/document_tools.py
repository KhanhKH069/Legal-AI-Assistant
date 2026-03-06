"""Document & E-Signature Tools — Document management and electronic signing"""

from datetime import datetime
import random
from typing import Any, Dict, Optional
from langchain_core.tools import tool

_DOCUMENTS_STATUS: dict = {}

# Default document templates for onboarding
_DOCUMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Labor Contract": {
        "name": "Hợp đồng lao động",
        "description": "Hợp đồng lao động chính thức giữa nhân viên và công ty",
        "required_for": "All employees",
        "template_fields": [
            "employee_name",
            "position",
            "department",
            "start_date",
            "salary_level",
        ],
        "validity_years": 1,
    },
    "NDA": {
        "name": "Thỏa thuận bảo mật thông tin (NDA)",
        "description": "Thỏa thuận không tiết lộ thông tin bí mật của công ty",
        "required_for": "All employees",
        "template_fields": ["employee_name", "position", "effective_date"],
        "validity_years": 3,
    },
    "Probation Agreement": {
        "name": "Hợp đồng thử việc",
        "description": "Hợp đồng trong thời gian thử việc (2 tháng)",
        "required_for": "New employees",
        "template_fields": [
            "employee_name",
            "position",
            "probation_start",
            "probation_end",
        ],
        "validity_years": None,
    },
    "Insurance Registration": {
        "name": "Đăng ký BHXH/BHYT",
        "description": "Đăng ký bảo hiểm xã hội và bảo hiểm y tế",
        "required_for": "All employees",
        "template_fields": ["employee_name", "personal_id", "dob", "address"],
        "validity_years": None,
    },
    "Bank Account Form": {
        "name": "Đăng ký tài khoản ngân hàng",
        "description": "Biểu mẫu đăng ký tài khoản ngân hàng để nhận lương",
        "required_for": "All employees",
        "template_fields": ["employee_name", "bank_name", "account_number", "branch"],
        "validity_years": None,
    },
}

# Mock signature status for employees
_SIGNATURE_STATUS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "EMP001": {
        "Labor Contract": {"signed": True, "signed_at": "2023-01-15T09:00:00"},
        "NDA": {"signed": True, "signed_at": "2023-01-15T09:05:00"},
        "Probation Agreement": {"signed": True, "signed_at": "2023-01-15T09:10:00"},
        "Insurance Registration": {"signed": True, "signed_at": "2023-01-16T10:00:00"},
        "Bank Account Form": {"signed": True, "signed_at": "2023-01-16T10:05:00"},
    },
    "EMP002": {
        "Labor Contract": {"signed": True, "signed_at": "2023-03-01T09:00:00"},
        "NDA": {"signed": True, "signed_at": "2023-03-01T09:05:00"},
        "Probation Agreement": {"signed": True, "signed_at": "2023-03-01T09:10:00"},
        "Insurance Registration": {"signed": False, "signed_at": None},
        "Bank Account Form": {"signed": True, "signed_at": "2023-03-02T10:00:00"},
    },
    "EMP003": {
        "Labor Contract": {"signed": False, "signed_at": None},
        "NDA": {"signed": False, "signed_at": None},
        "Probation Agreement": {"signed": True, "signed_at": "2024-06-01T09:00:00"},
        "Insurance Registration": {"signed": False, "signed_at": None},
        "Bank Account Form": {"signed": True, "signed_at": "2024-06-01T10:00:00"},
    },
}


@tool
def list_employee_documents(employee_id: str) -> str:
    """List all onboarding and HR documents for an employee, with signing status.

    Args:
        employee_id: The employee ID (e.g., EMP001).

    Returns:
        A list of all required documents and whether each has been signed.
    """
    eid = employee_id.strip().upper()
    status: Dict[str, Dict[str, Any]] = _SIGNATURE_STATUS.get(eid, {})

    if not status:
        # Default status for unknown employees — all pending
        status = {
            doc: {"signed": False, "signed_at": None} for doc in _DOCUMENT_TEMPLATES
        }

    lines = [f"📂 Danh Sách Tài Liệu HR của {eid}", "=" * 45]
    unsigned_count = 0
    for doc_key, template in _DOCUMENT_TEMPLATES.items():
        doc_status: Dict[str, Any] = status.get(
            doc_key, {"signed": False, "signed_at": None}
        )
        if doc_status["signed"]:
            signed_at: Optional[str] = doc_status["signed_at"]
            signed_date = signed_at[:10] if signed_at else ""
            lines.append(f"   ✅ {template['name']} — Đã ký ({signed_date})")
        else:
            lines.append(f"   ❌ {template['name']} — Chưa ký")
            unsigned_count += 1

    signed_count = len(_DOCUMENT_TEMPLATES) - unsigned_count
    lines.append(
        f"\n📊 Tiến độ: {signed_count}/{len(_DOCUMENT_TEMPLATES)} tài liệu đã ký"
    )
    if unsigned_count > 0:
        lines.append(
            f"⚠️ Còn {unsigned_count} tài liệu cần ký. "
            f"Dùng lệnh ký tài liệu để hoàn thành."
        )

    return "\n".join(lines)


@tool
def sign_document(employee_id: str, document_type: str) -> str:
    """Process an electronic signature (e-signature) for a specific HR document.

    Args:
        employee_id: The employee ID (e.g., EMP001).
        document_type: The document to sign. Options: 'Labor Contract',
                       'NDA', 'Probation Agreement',
                       'Insurance Registration', 'Bank Account Form'.

    Returns:
        Confirmation of the e-signature, including a simulated signing token.
    """
    eid = employee_id.strip().upper()

    if document_type not in _DOCUMENT_TEMPLATES:
        available = ", ".join(_DOCUMENT_TEMPLATES.keys())
        return (
            f"❌ Tài liệu '{document_type}' không hợp lệ.\n"
            f"Các tài liệu có thể ký: {available}"
        )

    template = _DOCUMENT_TEMPLATES[document_type]

    # Check if already signed
    emp_status: Dict[str, Dict[str, Any]] = _SIGNATURE_STATUS.get(eid, {})
    existing_status: Dict[str, Any] = emp_status.get(document_type, {})
    if existing_status.get("signed"):
        signed_at_val: Optional[str] = existing_status.get("signed_at")
        signed_at_str = signed_at_val[:10] if signed_at_val else ""
        return (
            f"ℹ️ Tài liệu '{template['name']}' "
            f"đã được ký vào {signed_at_str}.\n"
            f"Nếu cần ký lại, vui lòng liên hệ HR team."
        )

    # Generate mock e-signature token
    token = f"ESIG-{eid}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    verification_code = random.randint(100000, 999999)

    # Update in-memory status
    if eid not in _SIGNATURE_STATUS:
        _SIGNATURE_STATUS[eid] = {}
    _SIGNATURE_STATUS[eid][document_type] = {
        "signed": True,
        "signed_at": datetime.now().isoformat(),
    }

    return (
        f"✅ Ký tài liệu điện tử thành công!\n"
        f"   📄 Tài liệu: {template['name']}\n"
        f"   👤 Người ký: {eid}\n"
        f"   🔐 Mã ký số: {token}\n"
        f"   🔢 Mã xác thực: {verification_code}\n"
        f"   📅 Thời gian ký: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"   ✅ Tài liệu có giá trị pháp lý theo quy định về chữ ký điện tử.\n"
        f"Bản sao tài liệu đã ký sẽ được gửi đến email của bạn."
    )


@tool
def get_document_template(document_type: str) -> str:
    """Get information about an HR document template including purpose and required fields.

    Args:
        document_type: The document type. Options: 'Labor Contract',
                       'NDA', 'Probation Agreement',
                       'Insurance Registration', 'Bank Account Form'.

    Returns:
        Template description, required fields, and validity period.
    """
    if document_type not in _DOCUMENT_TEMPLATES:
        available = "\n".join(
            f"   • {k}: {v['name']}" for k, v in _DOCUMENT_TEMPLATES.items()
        )
        return (
            f"Tài liệu '{document_type}' không tồn tại. Các loại tài liệu:\n{available}"
        )

    t = _DOCUMENT_TEMPLATES[document_type]
    fields = ", ".join(t.get("template_fields", []))
    validity_years: Optional[int] = t.get("validity_years")
    validity = f"{validity_years} năm" if validity_years else "Không xác định"

    return (
        f"📄 Thông tin tài liệu: {t['name']}\n"
        f"   📋 Mô tả: {t['description']}\n"
        f"   👥 Đối tượng: {t['required_for']}\n"
        f"   📝 Trường thông tin cần điền: {fields}\n"
        f"   ⏳ Hiệu lực: {validity}"
    )
