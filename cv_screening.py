"""
CV Screening Module v2
Reads from job_requirements_config.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# For PDF parsing
try:
    import PyPDF2
except ImportError:
    print("Install: pip install PyPDF2")

# For DOCX parsing
try:
    from docx import Document
except ImportError:
    print("Install: pip install python-docx")

# ============================================
# JOB REQUIREMENTS LOADER
# ============================================

def load_job_requirements():
    """Load job requirements from config file"""
    config_file = Path("job_requirements_config.json")
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Convert detailed config to screening format
            requirements = {}
            
            for position, details in config.items():
                tech_skills = details.get('technical_skills', {})
                
                # Flatten required skills
                required = tech_skills.get('required', {})
                required_skills = []
                for category, skills in required.items():
                    if isinstance(skills, list):
                        required_skills.extend(skills)
                
                # Flatten preferred skills  
                preferred = tech_skills.get('preferred', {})
                preferred_skills = []
                for category, skills in preferred.items():
                    if isinstance(skills, list):
                        preferred_skills.extend(skills)
                
                # Get other requirements
                experience = details.get('experience', {})
                education = details.get('education', {})
                certifications = details.get('certifications', {})
                scoring = details.get('scoring', {})
                
                # Build requirements dict
                requirements[position] = {
                    'required_skills': [s.lower() for s in required_skills],
                    'preferred_skills': [s.lower() for s in preferred_skills],
                    'min_experience_years': experience.get('min_years', 0),
                    'education_keywords': [m.lower() for m in education.get('preferred_majors', [])],
                    'certifications': [c.lower() for c in certifications.get('preferred', [])],
                    'min_score': scoring.get('min_pass_score', 60)
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
            "education_keywords": ["computer science", "software engineering", "information technology"],
            "certifications": ["aws", "azure", "gcp"],
            "min_score": 60
        }
    }

# Load requirements at module import
JOB_REQUIREMENTS = load_job_requirements()

# ============================================
# CV PARSING FUNCTIONS
# ============================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text.lower()
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
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

def extract_cv_text(cv_path: str) -> str:
    """Extract text from CV (PDF or DOCX)"""
    if cv_path.endswith('.pdf'):
        return extract_text_from_pdf(cv_path)
    elif cv_path.endswith('.docx') or cv_path.endswith('.doc'):
        return extract_text_from_docx(cv_path)
    else:
        return ""

# ============================================
# CV ANALYSIS FUNCTIONS
# ============================================

def extract_years_of_experience(cv_text: str) -> int:
    """Extract years of experience from CV"""
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience.*?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+in',
        r'(\d+)\+?\s*năm kinh nghiệm',
    ]
    
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, cv_text)
        years.extend([int(y) for y in matches])
    
    return max(years) if years else 0

def check_skills(cv_text: str, skill_list: List[str]) -> Tuple[List[str], int]:
    """Check which skills from list are present in CV"""
    found_skills = []
    for skill in skill_list:
        if skill.lower() in cv_text:
            found_skills.append(skill)
    
    match_percentage = (len(found_skills) / len(skill_list) * 100) if skill_list else 0
    return found_skills, match_percentage

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

def score_cv(cv_path: str, position: str) -> Dict:
    """
    Score a CV for a specific position
    Returns: dict with score, breakdown, and recommendation
    """
    
    # Get job requirements
    if position not in JOB_REQUIREMENTS:
        return {
            "error": f"Position '{position}' not found in requirements database. Available positions: {list(JOB_REQUIREMENTS.keys())}"
        }
    
    requirements = JOB_REQUIREMENTS[position]
    
    # Extract CV text
    cv_text = extract_cv_text(cv_path)
    
    if not cv_text:
        return {
            "error": f"Could not extract text from CV: {cv_path}"
        }
    
    # Initialize scoring
    scores = {}
    total_score = 0
    max_score = 100
    
    # 1. Required Skills (30 points)
    required_skills, req_skill_pct = check_skills(cv_text, requirements["required_skills"])
    scores["required_skills"] = {
        "found": required_skills,
        "percentage": req_skill_pct,
        "points": (req_skill_pct / 100) * 30
    }
    total_score += scores["required_skills"]["points"]
    
    # 2. Preferred Skills (20 points)
    preferred_skills, pref_skill_pct = check_skills(cv_text, requirements["preferred_skills"])
    scores["preferred_skills"] = {
        "found": preferred_skills,
        "percentage": pref_skill_pct,
        "points": (pref_skill_pct / 100) * 20
    }
    total_score += scores["preferred_skills"]["points"]
    
    # 3. Experience (25 points)
    years_exp = extract_years_of_experience(cv_text)
    min_years = requirements["min_experience_years"]
    
    if years_exp >= min_years + 3:
        exp_points = 25
    elif years_exp >= min_years:
        exp_points = 20
    elif years_exp >= min_years - 1:
        exp_points = 15
    else:
        exp_points = 5
    
    scores["experience"] = {
        "years_found": years_exp,
        "years_required": min_years,
        "points": exp_points
    }
    total_score += exp_points
    
    # 4. Education (15 points)
    has_education = check_education(cv_text, requirements["education_keywords"])
    edu_points = 15 if has_education else 5
    
    scores["education"] = {
        "relevant": has_education,
        "points": edu_points
    }
    total_score += edu_points
    
    # 5. Certifications (10 points)
    found_certs = check_certifications(cv_text, requirements["certifications"])
    cert_points = min(len(found_certs) * 5, 10)
    
    scores["certifications"] = {
        "found": found_certs,
        "points": cert_points
    }
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
    
    return {
        "position": position,
        "total_score": round(total_score, 1),
        "max_score": max_score,
        "percentage": round((total_score / max_score) * 100, 1),
        "recommendation": recommendation,
        "status": status,
        "action": action,
        "breakdown": scores,
        "min_score": min_score
    }

# ============================================
# BATCH PROCESSING
# ============================================

def screen_all_applicants(db_file: str = "applicants_db.json") -> List[Dict]:
    """
    Screen all applicants in database
    Returns sorted list by score
    """
    
    if not Path(db_file).exists():
        return []
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            applicants = json.load(f)
    except Exception as e:
        print(f"Error loading database: {e}")
        return []
    
    results = []
    errors = []
    
    for applicant in applicants:
        cv_path = applicant.get('cv_path')
        position = applicant.get('position')
        name = applicant.get('name', 'Unknown')
        
        if cv_path and position:
            # Check if CV file exists
            if not Path(cv_path).exists():
                errors.append(f" CV not found: {name} - {cv_path}")
                continue
            
            score_result = score_cv(cv_path, position)
            
            if 'error' in score_result:
                errors.append(f" Error for {name}: {score_result['error']}")
            else:
                result = {
                    **applicant,
                    **score_result
                }
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
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    return results

# ============================================
# EXPORT RESULTS
# ============================================

def export_screening_results(results: List[Dict], output_file: str = "screening_results.json"):
    """Export screening results to JSON"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return output_file
    except Exception as e:
        print(f"Error exporting results: {e}")
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
        print(f" Successfully screened {len(results)} applicants\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['name']} - {result['position']}")
            print(f"   Score: {result['total_score']}/{result['max_score']} ({result['percentage']}%)")
            print(f"   Status: {result['status']}")
            print(f"   Action: {result['action']}")
            
            # Show breakdown
            breakdown = result['breakdown']
            print("   Breakdown:")
            print(f"     • Required Skills: {breakdown['required_skills']['points']:.1f}/30 ({breakdown['required_skills']['percentage']:.0f}%)")
            print(f"     • Preferred Skills: {breakdown['preferred_skills']['points']:.1f}/20 ({breakdown['preferred_skills']['percentage']:.0f}%)")
            print(f"     • Experience: {breakdown['experience']['points']}/25 ({breakdown['experience']['years_found']} years)")
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