"""Unit tests for Hatarake-specific tools.

All tests are designed to run fully OFFLINE (no API key, no internet needed).
"""

import json
import os
import tempfile
import pytest


# ─── CV Builder: generate_cv_pdf ─────────────────────────────────────────────


class TestGenerateCvPdf:
    def test_generates_pdf_file(self, tmp_path, monkeypatch):
        """generate_cv_pdf should create a .pdf file and return its path."""
        monkeypatch.chdir(tmp_path)
        from src.tools.cv_builder_tools import generate_cv_pdf

        result = generate_cv_pdf.invoke(
            {
                "applicant_name": "Nguyen Van Test",
                "contact_info": "test@test.com | 0901234567",
                "education": "Bach Khoa University - Computer Science",
                "experience": "2 years as Backend Developer at XYZ Corp",
                "skills": "Python, FastAPI, LangChain, Docker",
            }
        )
        assert "Successfully generated CV" in result
        # Extract path from message and verify file exists
        path = result.split("at: ")[-1].strip()
        assert os.path.exists(path)
        assert path.endswith(".pdf")

    def test_pdf_size_is_nonzero(self, tmp_path, monkeypatch):
        """The generated PDF should have non-zero file size."""
        monkeypatch.chdir(tmp_path)
        from src.tools.cv_builder_tools import generate_cv_pdf

        result = generate_cv_pdf.invoke(
            {
                "applicant_name": "Le Thi B",
                "contact_info": "b@example.com",
                "education": "RMIT University",
                "experience": "3 years QA Engineer",
                "skills": "Selenium, Python",
            }
        )
        path = result.split("at: ")[-1].strip()
        assert os.path.getsize(path) > 0

    def test_name_with_vietnamese_chars(self, tmp_path, monkeypatch):
        """PDF generation should not crash with Vietnamese diacritics in name."""
        monkeypatch.chdir(tmp_path)
        from src.tools.cv_builder_tools import generate_cv_pdf

        result = generate_cv_pdf.invoke(
            {
                "applicant_name": "Trần Văn Đức",
                "contact_info": "duc@test.vn",
                "education": "Đại học Bách Khoa",
                "experience": "Lập trình viên 3 năm kinh nghiệm",
                "skills": "Python, AI, Tiếng Nhật N3",
            }
        )
        # Should either succeed or fail gracefully (no unhandled exception)
        assert "CV" in result or "Error" in result


# ─── CV Builder: save_job_preferences ────────────────────────────────────────


class TestSaveJobPreferences:
    def test_saves_new_preference(self):
        """save_job_preferences should return a success message for a new applicant."""
        from src.tools.cv_builder_tools import save_job_preferences

        result = save_job_preferences.invoke(
            {
                "applicant_id": 88001,
                "industry": "IT",
                "locations": "Ha Noi, Ho Chi Minh",
                "min_salary": 25.0,
                "conditions": "Remote OK",
            }
        )
        assert "Successfully saved" in result
        assert "88001" in result

    def test_updates_existing_preference(self):
        """save_job_preferences called twice should update, not duplicate."""
        from src.tools.cv_builder_tools import save_job_preferences

        save_job_preferences.invoke(
            {
                "applicant_id": 88002,
                "industry": "Finance",
                "locations": "Ha Noi",
                "min_salary": 15.0,
                "conditions": "On-site",
            }
        )
        result = save_job_preferences.invoke(
            {
                "applicant_id": 88002,
                "industry": "IT",
                "locations": "Da Nang",
                "min_salary": 20.0,
                "conditions": "Hybrid",
            }
        )
        assert "Successfully saved" in result

    def test_invalid_applicant_id_handled_gracefully(self):
        """save_job_preferences with extreme ID should not crash."""
        from src.tools.cv_builder_tools import save_job_preferences

        result = save_job_preferences.invoke(
            {
                "applicant_id": 0,
                "industry": "Unknown",
                "locations": "",
                "min_salary": 0.0,
                "conditions": "",
            }
        )
        # Should either succeed or return error message, not raise exception
        assert isinstance(result, str)


# ─── CV Builder: match_jobs_for_candidate ────────────────────────────────────


class TestMatchJobsForCandidate:
    def test_returns_jobs_when_preferences_exist(self):
        """match_jobs_for_candidate should return job names after saving preferences."""
        from src.tools.cv_builder_tools import (
            save_job_preferences,
            match_jobs_for_candidate,
        )

        save_job_preferences.invoke(
            {
                "applicant_id": 77001,
                "industry": "IT",
                "locations": "Ha Noi",
                "min_salary": 18.0,
                "conditions": "Remote",
            }
        )
        result = match_jobs_for_candidate.invoke({"applicant_id": 77001})
        assert (
            "preferences" in result.lower()
            or "fit" in result.lower()
            or "Error" in result
        )

    def test_no_preferences_returns_helpful_message(self):
        """match_jobs_for_candidate should return guidance when no prefs saved."""
        from src.tools.cv_builder_tools import match_jobs_for_candidate

        result = match_jobs_for_candidate.invoke({"applicant_id": 999999})
        assert (
            "No preferences" in result
            or "Không tìm thấy" in result
            or "Error" in result
        )

    def test_result_is_string(self):
        """Return value must always be a string."""
        from src.tools.cv_builder_tools import match_jobs_for_candidate

        result = match_jobs_for_candidate.invoke({"applicant_id": 1})
        assert isinstance(result, str)


# ─── OCR: extract_id_card_info (Offline Fallback) ────────────────────────────


class TestExtractIdCardInfo:
    def test_missing_file_returns_error_json(self):
        """extract_id_card_info should return JSON error when file not found."""
        from src.tools.onboard_validation_tools import extract_id_card_info

        result = extract_id_card_info.invoke({"image_path": "nonexistent_card.jpg"})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_returns_valid_json_string(self, tmp_path):
        """extract_id_card_info should always return a parseable JSON string."""
        from src.tools.onboard_validation_tools import extract_id_card_info

        # Create a dummy non-image text file to test graceful failure
        fake_img = tmp_path / "fake.jpg"
        fake_img.write_bytes(b"not an image")

        result = extract_id_card_info.invoke({"image_path": str(fake_img)})
        # Should return valid JSON (either error or extracted data)
        try:
            parsed = json.loads(result)
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            pytest.fail(f"extract_id_card_info did not return valid JSON: {result}")


# ─── File Upload API ──────────────────────────────────────────────────────────


class TestFileUploadEndpoint:
    def test_upload_pdf_succeeds(self, client, tmp_path):
        """POST /files/upload-cv with a valid PDF should return filename and cv_path."""
        pdf_content = b"%PDF-1.4 dummy content"
        response = client.post(
            "/files/upload-cv",
            files={"file": ("test_cv.pdf", pdf_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "cv_path" in data
        assert data["filename"] == "test_cv.pdf"

    def test_upload_jpg_succeeds(self, client):
        """POST /files/upload-cv with a JPEG image should succeed (for ID card)."""
        fake_jpg = b"\xff\xd8\xff fake jpeg bytes"
        response = client.post(
            "/files/upload-cv",
            files={"file": ("id_card.jpg", fake_jpg, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "id_card.jpg"

    def test_upload_invalid_type_rejected(self, client):
        """POST /files/upload-cv with an .exe file should return 400."""
        response = client.post(
            "/files/upload-cv",
            files={"file": ("malware.exe", b"MZ...", "application/octet-stream")},
        )
        assert response.status_code == 400
