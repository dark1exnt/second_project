from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from celery import Task

from app.config import settings
from app.tasks.celery_app import celery_app


@celery_app.task(
    name="tasks.send_registration_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_registration_email(self: Task, to_email: str, username: str) -> None:
    subject = "Welcome to Blog Marketplace"
    body = f"""
    <html>
        <body>
            Добро пожаловать, {username}!
            Вы успешно зарегистрировались на Blog Marketplace.
        </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.emails_from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.emails_from_email, to_email, msg.as_string())
    except Exception as exc:
        raise self.retry(exc=exc) from exc
