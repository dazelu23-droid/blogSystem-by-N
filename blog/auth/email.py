import os
import smtplib
from email.message import EmailMessage


def send_password_reset_email(to_email, reset_url, app=None):
    """Send a password reset link. Returns True if sent, False if SMTP is not configured."""
    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        if app and app.config.get("TESTING"):
            return False
        if app:
            app.logger.warning(
                "SMTP not configured; password reset email was not sent to %s", to_email
            )
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("SMTP_FROM", smtp_user or "noreply@localhost")

    message = EmailMessage()
    message["Subject"] = "Reset your blog password"
    message["From"] = from_addr
    message["To"] = to_email
    message.set_content(
        "You requested a password reset for your blog account.\n\n"
        f"Open this link to choose a new password (valid for 1 hour):\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if os.environ.get("SMTP_TLS", "1") == "1":
            server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(message)
    return True
