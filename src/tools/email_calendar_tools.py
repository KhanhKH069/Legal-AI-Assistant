def draft_interview_email(
    candidate_name: str, position: str, interview_time: str
) -> str:
    """Mock AI function to draft a professional interview invitation email."""

    # In a real app, this would use an LLM (GenAI) to generate the email
    # For now, we return a professional template

    email_body = f"""
Subject: Mời Phỏng Vấn - Vị trí {position} tại Paraline Software

Kính gửi bạn {candidate_name},

Cảm ơn bạn đã quan tâm và ứng tuyển vào vị trí {position} tại Paraline Software.
Qua quá trình sàng lọc hồ sơ tự động, chúng tôi nhận thấy kinh nghiệm và kỹ năng của bạn rất phù hợp với yêu cầu của vị trí này.

Chúng tôi trân trọng mời bạn tham gia buổi phỏng vấn trực tuyến với đội ngũ chuyên môn.
Thời gian dự kiến: {interview_time}

Vui lòng xác nhận lại nếu bạn có thể sắp xếp tham gia qua email này.
Nếu thời gian trên chưa phù hợp, xin phản hồi lại để chúng tôi sắp xếp lịch khác.

Trân trọng,
HR Team
Paraline Software
    """.strip()
    return email_body


def schedule_google_meet(candidate_emails: list) -> str:
    """Mock function to generate a Google Meet link."""
    # In a real app, calling Google Calendar API
    random_id = "xxx-yyyy-zzz"  # Mock ID
    return f"https://meet.google.com/{random_id}"
