import os
import smtplib
from email.message import EmailMessage


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
    message["Subject"] = "Verify your AI Knowledge Assistant account"
    message["From"] = sender
    message["To"] = recipient

    message.set_content(
        "Welcome to AI Knowledge Assistant!\n\n"
        "Please verify your email address by opening this link:\n\n"
        f"{verification_url}\n\n"
        "This link expires in 30 minutes. "
        "If you did not create this account, you can ignore this email."
    )

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)
