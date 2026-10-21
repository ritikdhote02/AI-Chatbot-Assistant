import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def build_verification_email_html(verification_url: str) -> str:
    """Generate a modern styled HTML email matching Chat Point design."""
    template_path = TEMPLATES_DIR / "verification_email.html"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
        return template.replace("{{verification_url}}", verification_url)

    return f'<p><a href="{verification_url}">Verify Email Address</a></p>'


def send_verification_email(
    recipient: str,
    verification_url: str,
) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM_EMAIL", username)

    if not all([username, password, sender]):
        raise RuntimeError("SMTP configuration is incomplete.")

    message = EmailMessage()
    message["Subject"] = "Verify your Chat Point account"
    message["From"] = sender
    message["To"] = recipient

    # Plain-text fallback for text-only email clients
    plain_text = (
        "Welcome to Chat Point!\n\n"
        "Please verify your email address by opening this link:\n\n"
        f"{verification_url}\n\n"
        "This link expires in 30 minutes. "
        "If you did not create this account, you can ignore this email."
    )
    message.set_content(plain_text)

    # Modern HTML formatted email matching our frontend style
    html_content = build_verification_email_html(verification_url)
    message.add_alternative(html_content, subtype="html")

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)
