from langchain_core.tools import tool
import random
import os
import json
from src.core.config import config

try:
    import google.generativeai as genai

    if config.google_api_key:
        genai.configure(api_key=config.google_api_key)
except ImportError:
    pass


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


@tool
def extract_id_card_info(image_path: str) -> str:
    """Extract structured information from an ID Card or Residence Card image using Vision AI.

    - image_path: Path to the image file (jpg/png)

    Returns a JSON string containing fields like name, dob, nationality, visa_status, expiration_date.
    """
    if not os.path.exists(image_path):
        return json.dumps({"error": f"Image not found at {image_path}"})

    if config.enable_offline_mode or not config.google_api_key:
        try:
            import easyocr
            import re

            # Use gpu=False for safer deployment if no CUDA available
            reader = easyocr.Reader(["en", "vi", "ja"], gpu=False)
            results = reader.readtext(image_path, detail=0)
            text_data = " ".join(results)

            # Simple regex heuristics for extracting data
            name_match = re.search(r"(?i)(name|họ và tên)[:\s]+([A-Z\s]+)", text_data)
            dob_match = re.search(r"(\d{2,4}[/-]\d{1,2}[/-]\d{1,2})", text_data)

            name = name_match.group(2).strip() if name_match else "N/A"
            dob = dob_match.group(1).strip() if dob_match else "N/A"

            return json.dumps(
                {
                    "name": name,
                    "dob": dob,
                    "nationality": "N/A (Offline Regex fallback)",
                    "visa_status": "N/A (Offline Regex fallback)",
                    "expiration_date": "N/A (Offline Regex fallback)",
                    "raw_text": text_data[:200],
                }
            )
        except Exception as e:
            return json.dumps(
                {"error": f"Offline OCR failed: {str(e)}", "name": "N/A (Offline mode)"}
            )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        myfile = genai.upload_file(image_path)

        prompt = """
        You are a highly accurate ID card parsing system.
        Analyze this ID card (Residence Card or National ID) and extract the following fields in JSON format:
        - name (Full name)
        - dob (Date of birth)
        - nationality (Country of origin)
        - visa_status (Status of Residence)
        - expiration_date (Period of validity)

        Return ONLY a valid JSON object.
        """

        response = model.generate_content([myfile, prompt])
        text = response.text

        # clean JSON block if any
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return text.strip()
    except Exception as e:
        return json.dumps({"error": str(e)})
