from langchain_core.tools import tool
import json
import os
from datetime import datetime, UTC
from fpdf import FPDF
from src.db import session_scope
from src.db_models import JobPreference, Applicant

# Ensure fonts are available for Vietnamese
# In a real system we would use a TTF font like Arial or DejaVu
# Since we don't have TTF files here easily, we'll just try to use default
# If Vietnamese text breaks, we might need to add a TTF file later.
# For now, let's keep it simple. We can use FPDF's built in fonts. FPDF2 supports unicode better if we add font.


@tool
def generate_cv_pdf(
    applicant_name: str, contact_info: str, education: str, experience: str, skills: str
) -> str:
    """Generate a formatted PDF CV from candidate information provided via chat.

    Args:
        applicant_name: The full name of the applicant.
        contact_info: Email, phone, address, etc.
        education: Summary of education.
        experience: Summary of work experience.
        skills: List or summary of skills.

    Returns:
        The path to the generated PDF file.
    """
    try:
        os.makedirs("documents", exist_ok=True)
        pdf_path = f"documents/CV_{applicant_name.replace(' ', '_')}_{int(datetime.now(UTC).timestamp())}.pdf"

        pdf = FPDF()
        pdf.add_page()
        # Load custom Vietnamese font to prevent Unicode errors
        font_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "fonts",
            "Roboto-Regular.ttf",
        )
        has_roboto = os.path.exists(font_path)
        if has_roboto:
            pdf.add_font("Roboto", "", font_path)
            # map bold to regular to avoid crash (only regular downloaded)
            pdf.add_font("Roboto", "B", font_path)
            pdf.set_font("Roboto", size=16, style="B")
        else:
            pdf.set_font("helvetica", "B", 16)

        pdf.cell(0, 10, text="RESUME / CV", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_auto_page_break(auto=True, margin=15)

        # Header
        pdf.cell(0, 10, applicant_name, align="C", new_x="LMARGIN", new_y="NEXT")

        if has_roboto:
            pdf.set_font("Roboto", size=11)
        else:
            pdf.set_font("helvetica", "", 11)

        pdf.cell(0, 10, contact_info, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # Sections
        def add_section(title, content):
            if has_roboto:
                pdf.set_font("Roboto", "B", 12)
            else:
                pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            if has_roboto:
                pdf.set_font("Roboto", "", 11)
            else:
                pdf.set_font("helvetica", "", 11)
            pdf.multi_cell(0, 6, content)
            pdf.ln(5)

        add_section("Education", education)
        add_section("Experience", experience)
        add_section("Skills", skills)

        pdf.output(pdf_path)
        return f"Successfully generated CV at: {pdf_path}"
    except Exception as e:
        return f"Error generating CV: {str(e)}"


@tool
def save_job_preferences(
    applicant_id: int, industry: str, locations: str, min_salary: float, conditions: str
) -> str:
    """Save or update the job preferences for an applicant in the database.

    Args:
        applicant_id: Database ID of the applicant.
        industry: Preferred industry or job role.
        locations: Comma-separated list of preferred locations.
        min_salary: Minimum expected salary in millions VNĐ or JPY (keep unit consistent).
        conditions: Other conditions (e.g. Remote, No overtime).

    Returns:
        Status message.
    """
    try:
        with session_scope() as session:
            # Check if preference already exists
            from sqlmodel import select

            pref = session.exec(
                select(JobPreference).where(JobPreference.applicant_id == applicant_id)
            ).first()
            if pref:
                pref.industry = industry
                pref.locations = locations
                pref.min_salary = min_salary
                pref.conditions = conditions
            else:
                pref = JobPreference(
                    applicant_id=applicant_id,
                    industry=industry,
                    locations=locations,
                    min_salary=min_salary,
                    conditions=conditions,
                )
                session.add(pref)

            return (
                f"Successfully saved job preferences for applicant ID {applicant_id}."
            )
    except Exception as e:
        return f"Error saving job preferences: {str(e)}"


@tool
def match_jobs_for_candidate(applicant_id: int) -> str:
    """Match existing job requirements against a candidate's saved preferences.

    Args:
        applicant_id: The ID of the applicant.

    Returns:
        A list of matching job positions.
    """
    try:
        with session_scope() as session:
            from sqlmodel import select

            pref = session.exec(
                select(JobPreference).where(JobPreference.applicant_id == applicant_id)
            ).first()
            if not pref:
                return "No preferences found for this applicant. Please ask them for their preferences first."

            pref_ind = pref.industry
            pref_sal = pref.min_salary

        # Load jobs
        config_path = "job_requirements_config.json"
        if not os.path.exists(config_path):
            return f"No job postings available. Config not found at {config_path}"

        with open(config_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        matches = []
        for pos_name, data in jobs.items():
            matches.append(pos_name)

        top_matches = matches[:5]
        return (
            f"Based on preferences (Industry: {pref_ind}, Salary: {pref_sal}), the following positions might be a good fit:\n"
            + "\n".join([f"- {m}" for m in top_matches])
        )

    except Exception as e:
        return f"Error matching jobs: {str(e)}"
