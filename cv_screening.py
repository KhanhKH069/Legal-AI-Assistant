"""
CV Screening Module v2
Reads from job_requirements_config.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

# For PDF parsing
try:
    import pdfplumber  # noqa: F401
except ImportError:
    print("Install: uv pip install pdfplumber")

# For DOCX parsing
try:
    from docx import Document
except ImportError:
    print("Install: uv pip install python-docx")

# For Semantic Scoring
_semantic_model = None

# Preferred: multilingual-e5-large (much better for Vietnamese)
# Fallback: paraphrase-multilingual-MiniLM-L12-v2 (smaller, older)
_PREFERRED_EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
_FALLBACK_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            try:
                print(f"  [Offline Scoring] Loading {_PREFERRED_EMBEDDING_MODEL}...")
                _semantic_model = SentenceTransformer(_PREFERRED_EMBEDDING_MODEL)
                print(
                    "  [Offline Scoring] Multilingual-E5-Large loaded (best Vietnamese support)"
                )
            except Exception:
                print(
                    f"  [Offline Scoring] Falling back to {_FALLBACK_EMBEDDING_MODEL}..."
                )
                _semantic_model = SentenceTransformer(_FALLBACK_EMBEDDING_MODEL)
        except ImportError:
            print(
                "  [Offline Scoring] SentenceTransformer not installed. Semantic scoring disabled."
            )
            return None
    return _semantic_model


# ============================================
# JOB REQUIREMENTS LOADER
# ============================================


def load_job_requirements():
    """Load job requirements from config file"""
    config_file = Path("job_requirements_config.json")

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Convert detailed config to screening format
            requirements = {}

            for position, details in config.items():
                tech_skills = details.get("technical_skills", {})

                # Flatten required skills
                required = tech_skills.get("required", {})
                required_skills = []
                for category, skills in required.items():
                    if isinstance(skills, list):
                        required_skills.extend(skills)

                # Flatten preferred skills
                preferred = tech_skills.get("preferred", {})
                preferred_skills = []
                for category, skills in preferred.items():
                    if isinstance(skills, list):
                        preferred_skills.extend(skills)

                # Get other requirements
                experience = details.get("experience", {})
                education = details.get("education", {})
                certifications = details.get("certifications", {})
                scoring = details.get("scoring", {})

                # Build requirements dict
                requirements[position] = {
                    "required_skills": [s.lower() for s in required_skills],
                    "preferred_skills": [s.lower() for s in preferred_skills],
                    "min_experience_years": experience.get("min_years", 0),
                    "education_keywords": [
                        m.lower() for m in education.get("preferred_majors", [])
                    ],
                    "certifications": [
                        c.lower() for c in certifications.get("preferred", [])
                    ],
                    "min_score": scoring.get("min_pass_score", 60),
                }

            print(f" Loaded {len(requirements)} positions from config")
            return requirements

        except Exception as e:
            print(f"  Error loading config: {e}")
            return get_default_requirements()
    else:
        print("  Config file not found, using default requirements")
        return get_default_requirements()


def get_default_requirements():
    """Fallback default requirements"""
    return {
        "Software Engineer": {
            "required_skills": ["python", "javascript", "java", "sql", "git"],
            "preferred_skills": ["react", "nodejs", "django", "flask", "docker"],
            "min_experience_years": 2,
            "education_keywords": [
                "computer science",
                "software engineering",
                "information technology",
            ],
            "certifications": ["aws", "azure", "gcp"],
            "min_score": 60,
        }
    }


# Load requirements at module import
JOB_REQUIREMENTS = load_job_requirements()

# ============================================
# CV PARSING FUNCTIONS
# ============================================


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file using PyMuPDF for block-based layout parsing"""
    try:
        import fitz

        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                blocks = page.get_text("blocks")
                # Sort blocks vertically then horizontally
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    if b[6] == 0:  # 0 means text block
                        text += b[4] + "\n"
        return text.lower()
    except ImportError:
        # Fallback to pdfplumber
        try:
            import pdfplumber

            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text.lower()
        except ImportError:
            # Final fallback: pypdf (modern replacement for PyPDF2)
            try:
                from pypdf import PdfReader

                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text.lower()
            except Exception:
                return ""
        except Exception:
            return ""
    except Exception as e:
        try:
            print(
                f"Error reading PDF {pdf_path}: {e}".encode("utf-8", "ignore").decode(
                    "utf-8"
                )
            )
        except Exception:
            pass
        return ""


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(docx_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.lower()
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
        return ""


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image (PNG, JPG, JPEG) using Gemini Vision or EasyOCR fallback."""
    from src.core.config import config

    # 1. Try Gemini Vision (Online Mode)
    if not config.enable_offline_mode and config.google_api_key:
        try:
            import google.generativeai as genai
            import PIL.Image

            genai.configure(api_key=config.google_api_key)
            # Use gemini-1.5-flash for vision tasks
            model = genai.GenerativeModel("gemini-1.5-flash")

            img = PIL.Image.open(image_path)
            prompt = "Please extract all the text from this image exactly as it appears. Return only the text without any markdown formatting."

            response = model.generate_content([prompt, img])
            if response.text:
                return response.text.lower()
        except Exception as e:
            print(f"Gemini Vision API failed: {e}. Falling back to EasyOCR.")

    # 2. Try EasyOCR (Offline Mode or Fallback)
    try:
        import easyocr
        import numpy as np  # noqa: F401
        import cv2  # noqa: F401

        # Initialize reader once (this will download model weights on first run)
        # Using English and Vietnamese
        reader = easyocr.Reader(["vi", "en"], gpu=False)

        # EasyOCR works best with OpenCV images
        result = reader.readtext(image_path, detail=0)
        text = "\n".join(result)
        return text.lower()
    except ImportError:
        print("Install: python -m pip install easyocr opencv-python")
        return ""
    except Exception as e:
        print(f"Error reading Image {image_path}: {e}")
        return ""


def extract_cv_text(cv_path: str) -> str:
    """Extract text from CV (PDF, DOCX, PNG, JPG, JPEG)"""
    cv_path_lower = cv_path.lower()
    if cv_path_lower.endswith(".pdf"):
        return extract_text_from_pdf(cv_path)
    elif cv_path_lower.endswith(".docx") or cv_path_lower.endswith(".doc"):
        return extract_text_from_docx(cv_path)
    elif (
        cv_path_lower.endswith(".png")
        or cv_path_lower.endswith(".jpg")
        or cv_path_lower.endswith(".jpeg")
    ):
        return extract_text_from_image(cv_path)
    else:
        return ""


# ============================================
# CV ANALYSIS FUNCTIONS
# ============================================


def extract_years_of_experience(cv_text: str) -> int:
    """Extract years of experience from CV"""
    patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
        r"experience.*?(\d+)\+?\s*years?",
        r"(\d+)\+?\s*years?\s+in",
        r"(\d+)\+?\s*năm kinh nghiệm",
    ]

    years = []
    for pattern in patterns:
        matches = re.findall(pattern, cv_text.lower())
        years.extend([int(y) for y in matches])

    from datetime import datetime
    current_year = datetime.now().year
    
    year_matches = re.findall(r"\b(19\d{2}|20\d{2})\b", cv_text)
    year_matches = sorted(list(set([int(y) for y in year_matches])))
    
    if year_matches:
        min_year = min(year_matches)
        max_year = max(year_matches)
        
        if re.search(r"-\s*present|to\s*present|-\s*hiện tại|đến\s*nay|nay|hiện nay", cv_text.lower()):
            max_year = max(max_year, current_year)
            
        if 1980 <= min_year <= current_year and min_year <= max_year:
            calc_years = max_year - min_year
            if calc_years > 0:
                years.append(calc_years)

    return max(years) if years else 0


def check_skills(cv_text: str, skill_list: List[str]) -> Tuple[List[str], float]:
    """Check which skills from list are present in CV"""
    found_skills = []
    cv_text_lower = cv_text.lower()

    for skill in skill_list:
        clean_skill = re.sub(r'\(.*?\)', '', skill).lower().strip()
        parts = [p.strip() for p in re.split(r"[/,]", clean_skill) if p.strip()]

        matched = False
        for part in parts:
            if not part:
                continue

            fluff_words = ["programming", "principles", "concepts", "fundamentals", "basics", "usage", "framework", "library", "methodology", "familiarity", "exposure", "knowledge of", "development"]
            for fluff in fluff_words:
                part = part.replace(fluff, "").strip()

            if not part:
                continue

            if len(part) <= 3 or part in ["java", "c++", "c#"]:
                escaped = re.escape(part)
                if re.search(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", cv_text_lower):
                    matched = True
                    break
            else:
                if part in cv_text_lower:
                    matched = True
                    break
                    
                words = part.split()
                if len(words) >= 3:
                    if words[0] in cv_text_lower and words[-1] in cv_text_lower:
                        matched = True
                        break

        if matched:
            found_skills.append(skill)

    match_percentage = (len(found_skills) / len(skill_list) * 100) if skill_list else 0
    return found_skills, match_percentage


def extract_section(cv_text: str, keywords: List[str]) -> str:
    """Extract a specific section from CV text."""
    lines = cv_text.split("\n")
    section_text = []
    in_section = False

    stop_keywords = [
        "education", "học vấn", "experience", "kinh nghiệm", "work experience",
        "skills", "kỹ năng", "certifications", "chứng chỉ", "activities",
        "hoạt động", "references", "người tham chiếu", "projects", "dự án",
        "highlight project", "personal projects", "summary", "about me", "tóm tắt",
        "achievement", "thành tích", "objective", "mục tiêu"
    ]
    
    keywords_lower = [k.lower() for k in keywords]

    for line in lines:
        lower_line = line.strip().lower()
        if not lower_line:
            continue

        is_target_header = False
        if len(lower_line) < 60:
            for kw in keywords_lower:
                if kw in lower_line:
                    is_target_header = True
                    break

        if is_target_header:
            in_section = True
            continue

        is_stop_header = False
        if in_section and len(lower_line) < 60:
            for stop_kw in stop_keywords:
                if stop_kw not in keywords_lower and stop_kw in lower_line:
                    is_stop_header = True
                    break

            if is_stop_header:
                break
            
            section_text.append(line.strip())

    return "\n".join(section_text)


def check_education(cv_text: str, education_keywords: List[str]) -> bool:
    """Check if CV contains relevant education"""
    for keyword in education_keywords:
        if keyword.lower() in cv_text:
            return True
    return False


def check_certifications(cv_text: str, cert_keywords: List[str]) -> List[str]:
    """Check for certifications"""
    found_certs = []
    for cert in cert_keywords:
        if cert.lower() in cv_text:
            found_certs.append(cert)
    return found_certs


# ============================================
# MAIN SCORING FUNCTION
# ============================================


def score_cv(cv_path: str, position: str, progress_callback=None) -> Dict[str, Any]:
    """
    Scores a CV against the specified position requirements.
    Optionally reports progress back via progress_callback(message, percentage).
    """
    if progress_callback:
        progress_callback(f"Bắt đầu xử lý CV cho vị trí: {position}", 5)

    # Get job requirements
    if position not in JOB_REQUIREMENTS:
        # Try to find a fuzzy match (e.g. 'AI Intern' -> 'AI Engineer - Intern')
        matched_pos = None

        pos_words = set(position.lower().replace("-", " ").split())

        for req_pos in JOB_REQUIREMENTS.keys():
            req_words = set(req_pos.lower().replace("-", " ").split())
            # If all words in candidate's position are in the requirement position
            if pos_words.issubset(req_words):
                matched_pos = req_pos
                break

        if matched_pos:
            print(
                f"Warning: Exact position '{position}' not found, using '{matched_pos}' instead."
            )
            position = matched_pos
        else:
            # Fallback: Just use a generic one like 'Software Engineer - Junior'
            print(
                f"Warning: Position '{position}' not found. Falling back to Software Engineer - Junior"
            )
            position = "Software Engineer - Junior"

    requirements = JOB_REQUIREMENTS[position]

    # Extract CV text
    if progress_callback:
        progress_callback("Đang đọc nội dung file...", 10)
    cv_text = extract_cv_text(cv_path)

    if not cv_text:
        return {"error": f"Could not extract text from CV: {cv_path}"}

    # Initialize scoring
    scores = {}
    total_score = 0
    max_score = 100

    # 1. Required Skills (20 points)
    required_skills, req_skill_pct = check_skills(
        cv_text, requirements["required_skills"]
    )
    scores["required_skills"] = {
        "found": required_skills,
        "percentage": req_skill_pct,
        "points": (req_skill_pct / 100) * 20,
    }
    total_score += scores["required_skills"]["points"]  # type: ignore[operator]

    # 2. Preferred Skills (10 points)
    preferred_skills, pref_skill_pct = check_skills(
        cv_text, requirements["preferred_skills"]
    )
    scores["preferred_skills"] = {
        "found": preferred_skills,
        "percentage": pref_skill_pct,
        "points": (pref_skill_pct / 100) * 10,
    }
    total_score += scores["preferred_skills"]["points"]  # type: ignore[operator]

    if progress_callback:
        progress_callback("Đang chấm điểm kinh nghiệm làm việc...", 30)
    # 3. Experience (15 points)
    years_exp = extract_years_of_experience(cv_text)
    min_years = requirements["min_experience_years"]

    if years_exp >= min_years + 2:
        exp_points = 15
    elif years_exp >= min_years + 1:
        exp_points = 10
    elif years_exp >= min_years:
        exp_points = 5
    else:
        exp_points = 0

    scores["experience"] = {
        "years_found": years_exp,
        "years_required": min_years,
        "points": exp_points,
    }
    total_score += exp_points

    # 4. Education (10 points)
    has_education = check_education(cv_text, requirements["education_keywords"])
    edu_points = 10 if has_education else 0

    scores["education"] = {"relevant": has_education, "points": edu_points}
    total_score += edu_points

    # 5. Certifications (5 points)
    found_certs = check_certifications(cv_text, requirements["certifications"])
    cert_points = min(len(found_certs) * 2.5, 5)

    scores["certifications"] = {"found": found_certs, "points": cert_points}
    total_score += cert_points

    # Determine recommendation
    min_score = requirements["min_score"]

    if total_score >= min_score + 20:
        recommendation = "STRONG_PASS"
        status = " Highly Recommended"
        action = "Schedule interview ASAP"
    elif total_score >= min_score:
        recommendation = "PASS"
        status = " Recommended"
        action = "Schedule interview"
    elif total_score >= min_score - 10:
        recommendation = "MAYBE"
        status = " Consider"
        action = "Review manually"
    else:
        recommendation = "REJECT"
        status = " Not Recommended"
        action = "Send rejection email"

    if progress_callback:
        progress_callback("Đang sinh câu hỏi phỏng vấn...", 60)
    # 6. Generate Interview Questions (Phase 3 Feature)
    missing_skills = [
        s for s in requirements["required_skills"] if s.lower() not in cv_text.lower()
    ]
    interview_questions = []

    from src.core.config import config

    if not config.enable_offline_mode and config.google_api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.google_api_key)
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"Sinh ra 5 câu hỏi phỏng vấn hóc búa bằng tiếng Việt dành riêng cho ứng viên ứng tuyển vị trí {position}. Ứng viên đang thiếu các kỹ năng sau: {', '.join(missing_skills)}. Hãy đặt câu hỏi xoáy sâu vào các kỹ năng này để kiểm tra xem họ có thực sự không biết hay không. Trả về đúng 5 câu dạng JSON list (mảng các string), không markdown."
            response = gemini_model.generate_content(prompt)
            import json

            try:
                # Strip markdown code blocks if any
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:-3].strip()
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:-3].strip()
                interview_questions = json.loads(clean_text)
            except Exception:
                # Fallback to simple split
                interview_questions = [
                    q.strip()
                    for q in response.text.split("\n")
                    if q.strip() and ("?" in q or len(q) > 10)
                ]
        except Exception as e:
            print(f"Error generating interview questions with Gemini: {e}")

    if not interview_questions:
        # Offline Mode fallback: rule-based questions
        interview_questions = [
            f"Theo CV, bạn có vẻ chưa có nhiều kinh nghiệm với {skill}. Bạn dự định học hỏi kỹ năng này như thế nào?"
            for skill in missing_skills[:3]
        ]
        if len(interview_questions) < 5:
            interview_questions.extend(
                [
                    "Mô tả dự án lớn nhất bạn từng tham gia và vai trò của bạn trong đó?",
                    "Bạn xử lý thế nào khi gặp bất đồng quan điểm với quản lý về mặt kỹ thuật?",
                    "Điều gì khiến bạn nghĩ mình phù hợp với vị trí này?",
                ][: 5 - len(interview_questions)]
            )

    # 6. Extract raw Skills and Projects for LLM
    raw_projects = extract_section(
        cv_text,
        [
            "projects",
            "dự án",
            "highlight project",
            "personal projects",
            "academic projects",
        ],
    )
    raw_skills = extract_section(
        cv_text, ["skills", "kỹ năng", "core skills", "technical skills"]
    )

    if progress_callback:
        progress_callback("Đang đánh giá Semantic Match bằng Vector Database...", 75)
    # 7. Semantic Project Score (40 points)
    semantic_score = 0
    semantic_model = get_semantic_model()
    if semantic_model and (raw_projects or raw_skills):
        target_text = " ".join(
            requirements["required_skills"] + requirements["preferred_skills"]
        )
        cv_content = raw_skills + "\n" + raw_projects
        content_len = len(cv_content.strip())
        if content_len > 50:
            from sentence_transformers import util

            target_emb = semantic_model.encode(target_text)

            # Split into chunks (paragraphs/bullet points) to find the most relevant project
            chunks = [c.strip() for c in cv_content.split("\n") if len(c.strip()) > 20]
            if chunks:
                chunk_embs = semantic_model.encode(chunks)
                similarities = util.cos_sim(target_emb, chunk_embs)[0]
                max_sim = similarities.max().item()

                # Map similarity from [0.3, 0.6] to [0, 40]
                mapped_score = max(0, min(40, (max_sim - 0.3) / 0.3 * 40))

                # Depth Multiplier
                depth_multiplier = max(0.8, min(1.5, content_len / 1000.0))

                final_semantic = mapped_score * depth_multiplier
                semantic_score = round(min(40.0, final_semantic), 1)

    scores["semantic_match"] = {"points": semantic_score}
    total_score += semantic_score

    if progress_callback:
        progress_callback("Đã hoàn tất đánh giá CV.", 100)

    return {
        "position": position,
        "total_score": round(total_score, 1),
        "max_score": max_score,
        "percentage": round((total_score / max_score) * 100, 1),
        "recommendation": recommendation,
        "status": status,
        "action": action,
        "breakdown": scores,
        "interview_questions": interview_questions,
        "min_score": min_score,
        "raw_projects": raw_projects,
        "raw_skills": raw_skills,
    }


# ============================================
# BATCH PROCESSING
# ============================================


def screen_all_applicants(
    db_file: str = "applicants_db.json", progress_callback=None
) -> List[Dict]:
    """
    Screen all applicants in database (SQLite first, fallback to JSON)
    Returns sorted list by score
    """
    applicants_data = []

    try:
        from src.db import get_session
        from src.db_models import Applicant
        from sqlmodel import select

        session = get_session()
        db_applicants = session.exec(select(Applicant)).all()
        if db_applicants:
            print(f" Loaded {len(db_applicants)} applicants from SQLite Database")
            for app in db_applicants:
                applicants_data.append(
                    {
                        "id": app.id,
                        "name": app.name,
                        "email": app.email,
                        "phone": app.phone,
                        "position": app.position,
                        "cv_path": app.cv_path,
                        "status": app.status,
                    }
                )
    except ImportError:
        pass
    except Exception as e:
        print(f" Could not load from SQLite: {e}")

    # Fallback to JSON if no SQLite applicants found
    if not applicants_data and Path(db_file).exists():
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                applicants_data = json.load(f)
                print(f" Loaded {len(applicants_data)} applicants from {db_file}")
        except Exception as e:
            print(f" Error loading JSON database: {e}")

    if not applicants_data:
        return []

    results = []
    errors = []

    for applicant in applicants_data:
        cv_path = applicant.get("cv_path")
        position = applicant.get("position")
        name = applicant.get("name", "Unknown")

        if cv_path and position:
            # Check if CV file exists. It might be relative to data dir
            from src.core.storage import get_storage_service
            storage = get_storage_service()
            try:
                local_path_str = storage.get_local_path(cv_path)
                real_cv_path = Path(local_path_str)
                if not real_cv_path.exists():
                    errors.append(f" CV not found: {name} - {cv_path}")
                    continue
            except Exception as e:
                errors.append(f" Error retrieving CV: {name} - {e}")
                continue

            # Calculate base percentage for this applicant
            idx = applicants_data.index(applicant)
            total = len(applicants_data)
            base_pct = (idx / total) * 100
            step_pct = 100 / total

            def sub_callback(msg: str, sub_pct: float):
                if progress_callback:
                    final_pct = base_pct + (sub_pct / 100) * step_pct
                    # Format message nicely
                    progress_callback(f"[{name}] {msg}", final_pct)

            score_result = score_cv(
                str(real_cv_path), position, progress_callback=sub_callback
            )

            if "error" in score_result:
                errors.append(f" Error for {name}: {score_result['error']}")
            else:
                result = {**applicant, **score_result}
                results.append(result)
        else:
            errors.append(f" Missing cv_path or position for {name}")

    # Print errors if any
    if errors:
        print("\n  Errors during screening:")
        for error in errors:
            print(f"   {error}")
        print()

    # Sort by score (highest first)
    results.sort(key=lambda x: x["total_score"], reverse=True)

    return results


# ============================================
# EXPORT RESULTS
# ============================================


def export_screening_results(
    results: List[Dict], output_file: str = "screening_results.json"
):
    """Export screening results to JSON"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return output_file
    except Exception as e:
        print(f"Error exporting results: {e}")
        return None


def export_to_excel(results: List[Dict], output_file: str = "hr_screening_report.xlsx"):
    """Export screening results to Excel for HR dashboard"""
    try:
        import pandas as pd

        flat_results = []
        for r in results:
            bd = r.get("breakdown", {})
            flat = {
                "Name": r.get("name", ""),
                "Position": r.get("position", ""),
                "Total Score": r.get("total_score", 0),
                "Status": r.get("status", ""),
                "Action": r.get("action", ""),
                "Exp Points": bd.get("experience", {}).get("points", 0),
                "Years Exp": bd.get("experience", {}).get("years_found", 0),
                "Req Skills Points": bd.get("required_skills", {}).get("points", 0),
                "Pref Skills Points": bd.get("preferred_skills", {}).get("points", 0),
                "Semantic Points": bd.get("semantic_match", {}).get("points", 0),
                "Edu Points": bd.get("education", {}).get("points", 0),
                "Cert Points": bd.get("certifications", {}).get("points", 0),
                "CV Path": r.get("cv_path", ""),
            }
            flat_results.append(flat)

        df = pd.DataFrame(flat_results)
        df.to_excel(output_file, index=False)
        print(f" Exported Excel report to: {output_file}")
        return output_file
    except ImportError:
        print(" Pandas not installed. Cannot export to Excel.")
        return None
    except Exception as e:
        print(f" Error exporting Excel: {e}")
        return None


# ============================================
# MAIN FUNCTION
# ============================================

if __name__ == "__main__":
    print(" CV Screening System v2")
    print("=" * 50)
    print(f" Loaded {len(JOB_REQUIREMENTS)} positions")
    print()

    # Screen all applicants
    results = screen_all_applicants()

    if results:
        # Export to Excel
        export_to_excel(results)

        print(f" Successfully screened {len(results)} applicants\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']} - {result['position']}")
            print(
                f"   Score: {result['total_score']}/{result['max_score']} ({result['percentage']}%)"
            )
            print(f"   Status: {result['status']}")
            print(f"   Action: {result['action']}")

            # Show breakdown
            breakdown = result["breakdown"]
            print("   Breakdown:")
            print(
                f"     • Required Skills: {breakdown['required_skills']['points']:.1f}/30 ({breakdown['required_skills']['percentage']:.0f}%)"
            )
            print(
                f"     • Preferred Skills: {breakdown['preferred_skills']['points']:.1f}/20 ({breakdown['preferred_skills']['percentage']:.0f}%)"
            )
            print(
                f"     • Experience: {breakdown['experience']['points']}/25 ({breakdown['experience']['years_found']} years)"
            )
            print(f"     • Education: {breakdown['education']['points']}/15")
            print(f"     • Certifications: {breakdown['certifications']['points']}/10")
            print()

        # Export
        export_file = export_screening_results(results)
        if export_file:
            print(f" Results exported to: {export_file}")
    else:
        print(" No applicants found or all failed screening")
        print()
        print(" Troubleshooting:")
        print("   1. Check if applicants_db.json exists")
        print("   2. Verify CV files exist at paths in database")
        print("   3. Ensure job_requirements_config.json is present")
