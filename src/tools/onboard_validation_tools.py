from langchain_core.tools import tool
import random


@tool
def verify_onboarding_document(doc_type: str, file_status: str) -> str:
    """Verify an uploaded onboarding document (e.g., ID card, certificates) using AI OCR.

    Args:
        doc_type: Type of the document (e.g., "CCCD", "Tax", "Health Check").
        file_status: Simulated status of the uploaded file ("uploaded" or "missing").

    Returns:
        A string indicating the validation result.
    """
    if file_status != "uploaded":
        return f"Warning: No file uploaded for {doc_type}. Please upload the document first."

    # Mocking AI OCR validation logic
    if "CCCD" in doc_type.upper() or "ID" in doc_type.upper():
        is_valid = random.choice([True, True, False])  # 66% chance of success
        if is_valid:
            return f" AI OCR Verified: Valid {doc_type} detected. All required fields (Name, DOB, ID Number) are legible."
        else:
            return f" AI OCR Error: The {doc_type} image is blurry or missing the ID number. Please re-upload a clear photo."

    return f" Document {doc_type} received and flagged for manual HR review."
