import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "hr@paraline.vn")

    def send_email(
        self, to_email: str, subject: str, body_text: str, body_html: str = None
    ):
        if not self.host or not self.username or not self.password:
            # Fallback for dev mode / when SMTP is not configured
            logger.warning("SMTP config missing. Falling back to console output.")
            print("\n" + "=" * 50)
            print(f"📧 [MOCK EMAIL SENT]")
            print(f"To: {to_email}")
            print(f"From: {self.from_email}")
            print(f"Subject: {subject}")
            print("-" * 50)
            print(body_text)
            if body_html:
                print("--- [HTML Content] ---")
                print(body_html)
            print("=" * 50 + "\n")
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise e


def get_email_service() -> EmailService:
    return EmailService()
