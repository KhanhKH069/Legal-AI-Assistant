import os
import json
import redis
from celery import Celery
from sqlmodel import select
from src.core.config import config
from src.db import get_session
from src.db_models import ScreeningResult, Applicant
from cv_screening import screen_all_applicants

from src.core.logging_config import setup_logging
setup_logging()

# Initialize Celery
celery_app = Celery(
    "hr_agent_tasks",
    broker=config.redis_url,
    backend=config.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)

# Initialize Redis client for Pub/Sub
redis_client = redis.Redis.from_url(config.redis_url)


def broadcast_progress(message: str, progress: float, done: bool = False):
    """Publish progress to Redis channel so FastAPI can push to WebSockets."""
    channel = "screening_progress_global"
    payload = json.dumps({"message": message, "progress": progress, "done": done})
    try:
        redis_client.publish(channel, payload)
    except Exception as e:
        print(f"Failed to publish to redis: {e}")


@celery_app.task(name="run_screening_background_task")
def run_screening_background_task(applicant_id: int = None):
    """Background task to screen CVs using Celery."""
    try:

        def progress_callback(msg: str, pct: float):
            broadcast_progress(msg, pct)

        # This will query DB, score CVs using RAG/EasyOCR/Gemini
        results = screen_all_applicants(progress_callback=progress_callback)

        if results:
            session = get_session()

            # Clear old results
            if applicant_id is None:
                old_results = session.exec(select(ScreeningResult)).all()
                for r in old_results:
                    session.delete(r)
            else:
                old_results = session.exec(
                    select(ScreeningResult).where(
                        ScreeningResult.applicant_id == applicant_id
                    )
                ).all()
                for r in old_results:
                    session.delete(r)

            session.commit()

            for r in results:
                app_id = r.get("id")
                if applicant_id is not None and app_id != applicant_id:
                    continue

                if not app_id:
                    continue

                db_result = ScreeningResult(
                    applicant_id=app_id,
                    position=r.get("position", ""),
                    total_score=r.get("total_score", 0),
                    max_score=r.get("max_score", 100),
                    percentage=r.get("percentage", 0),
                    recommendation=r.get("recommendation", ""),
                    status=r.get("status", ""),
                    action=r.get("action", ""),
                    breakdown=r.get("breakdown", {}),
                    interview_questions=r.get("interview_questions", []),
                    min_score=r.get("min_score", 60),
                )
                session.add(db_result)

                # Update applicant status
                app = session.get(Applicant, app_id)
                if app:
                    app.status = "SCREENED"
                    session.add(app)

            session.commit()
            print(f"Successfully screened {len(results)} applicants and saved to DB.")

            # Send HR Notification Email (Manual Approval Workflow)
            from src.core.email_service import get_email_service
            email_svc = get_email_service()
            
            hr_email = os.getenv("SMTP_USERNAME")
            if hr_email:
                for r in results:
                    try:
                        name = r.get("name", "Ứng viên")
                        position = r.get("position", "vị trí ứng tuyển")
                        cand_email = r.get("email", "")
                        score = r.get("total_score", 0)
                        recommendation = r.get("recommendation", "")
                        
                        subject = f"[AI Report] Kết quả chấm CV - {name} - Vị trí: {position}"
                        
                        # Prepare Mailto link contents
                        import urllib.parse
                        
                        reject_subject = f"Thông báo Kết quả Ứng tuyển - Vị trí {position}"
                        reject_body = f"Kính gửi {name},\n\nCảm ơn bạn đã quan tâm và dành thời gian ứng tuyển vào vị trí {position} tại Paraline Software.\n\nSau khi xem xét kỹ lưỡng hồ sơ của bạn, chúng tôi rất tiếc phải thông báo rằng hồ sơ của bạn chưa hoàn toàn phù hợp với định hướng tuyển dụng của chúng tôi trong thời điểm hiện tại.\n\nChúng tôi đánh giá cao kỹ năng và kinh nghiệm của bạn, và sẽ lưu trữ hồ sơ của bạn trong hệ thống. Nếu có vị trí phù hợp hơn trong tương lai, chúng tôi sẽ chủ động liên hệ lại.\n\nChúc bạn nhiều sức khỏe và thành công trên con đường sự nghiệp.\n\nTrân trọng,\nHR Team\nParaline Software"
                        reject_link = f"mailto:{cand_email}?subject={urllib.parse.quote(reject_subject)}&body={urllib.parse.quote(reject_body)}"
                        
                        invite_subject = f"Thư Mời Phỏng Vấn - Vị trí {position} tại Paraline Software"
                        invite_body = f"Kính gửi {name},\n\nCảm ơn bạn đã quan tâm và ứng tuyển vào vị trí {position} tại Paraline Software.\nQua quá trình sàng lọc hồ sơ tự động, chúng tôi nhận thấy kinh nghiệm và kỹ năng của bạn rất phù hợp với yêu cầu của vị trí này.\n\nChúng tôi trân trọng mời bạn tham gia buổi phỏng vấn trực tuyến với đội ngũ chuyên môn.\nThời gian dự kiến: [ĐIỀN THỜI GIAN VÀO ĐÂY]\nLink Google Meet: [ĐIỀN LINK MEER VÀO ĐÂY]\n\nVui lòng tham gia đúng giờ và xác nhận lại nếu bạn có thể sắp xếp tham gia bằng cách reply email này.\n\nTrân trọng,\nHR Team\nParaline Software"
                        invite_link = f"mailto:{cand_email}?subject={urllib.parse.quote(invite_subject)}&body={urllib.parse.quote(invite_body)}"
                        
                        body_text = f"""Báo cáo kết quả chấm CV tự động:

Ứng viên {name} ({cand_email}) vừa ứng tuyển vị trí {position}.
- Điểm số: {score}/100
- Đánh giá AI: {recommendation}

Quyết định của bạn:
- TỪ CHỐI: Copy và dán link này vào trình duyệt để gửi thư từ chối: {reject_link}
- MỜI PHỎNG VẤN: Copy và dán link này vào trình duyệt để gửi thư mời phỏng vấn: {invite_link}
"""
                        
                        body_html = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                <h2>Báo cáo kết quả chấm CV tự động</h2>
                                <p>Ứng viên <strong>{name}</strong> (<a href="mailto:{cand_email}">{cand_email}</a>) vừa ứng tuyển vị trí <strong>{position}</strong>.</p>
                                <ul>
                                    <li><strong>Điểm số:</strong> {score}/100</li>
                                    <li><strong>Đánh giá AI:</strong> <span style="color: {'#e11d48' if recommendation == 'REJECT' else '#16a34a'}; font-weight: bold;">{recommendation}</span></li>
                                </ul>
                                
                                <h3>Quyết định của bạn:</h3>
                                <div style="margin-top: 20px;">
                                    <a href="{reject_link}" style="background-color: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 15px; font-weight: bold;">🚫 Gửi thư Từ chối</a>
                                    <a href="{invite_link}" style="background-color: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">✅ Gửi thư Mời phỏng vấn</a>
                                </div>
                                <p style="margin-top: 30px; font-size: 0.9em; color: #666;">
                                    * Khi bấm vào nút, hệ thống sẽ mở ứng dụng Mail của bạn với nội dung được điền sẵn. Bạn có thể chỉnh sửa lại trước khi gửi.
                                </p>
                            </body>
                        </html>
                        """
                        
                        email_svc.send_email(to_email=hr_email, subject=subject, body_text=body_text, body_html=body_html)
                    except Exception as email_err:
                        print(f"Failed to send HR notification email for {r.get('email')}: {email_err}")

            # Send completion signal
            broadcast_progress("Đã hoàn tất đánh giá toàn bộ CV!", 100, done=True)
            return {"status": "success", "screened": len(results)}

    except Exception as e:
        print(f"Error in Celery screening task: {e}")
        broadcast_progress(f"Lỗi: {str(e)}", 0, done=True)
        return {"status": "error", "error": str(e)}


@celery_app.task(name="score_single_cv_task", bind=True)
def score_single_cv_task(self, cv_path: str, position: str):
    """Background task to score a single CV for the Agent."""
    from cv_screening import score_cv

    try:

        def progress_cb(msg: str, pct: float):
            self.update_state(state="PROGRESS", meta={"message": msg, "percent": pct})

        result = score_cv(cv_path, position, progress_callback=progress_cb)
        return result
    except Exception as e:
        return {"error": str(e)}
