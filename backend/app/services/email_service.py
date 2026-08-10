"""Transactional email (PRD Ch3.14): password reset + user invitations.

Sends over SMTP using the configured host/port (Mailpit/SMTP sandbox in
development, AWS SES in production — configuration only, per Ch4.12). If
the SMTP endpoint is unreachable the email is logged and swallowed rather
than raising, so a down mail sink never blocks the underlying account
action (e.g. a user is still created even if the invitation email fails to
send — matching the graceful-degradation posture used elsewhere, PRD Ch9.21).
"""

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import logger


def _send(to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.smtp_user or "no-reply@cliniscribe.ai"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
            if settings.smtp_user and settings.smtp_password:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    except OSError as exc:
        logger.warning(f"Failed to send email to {to_email}: {exc}", extra={"route": "email_service"})


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    link = f"{settings.frontend_base_url}/reset-password?token={reset_token}"
    _send(
        to_email,
        "Reset your CliniScribe AI password",
        f"A password reset was requested for your account.\n\n"
        f"Reset your password: {link}\n\n"
        f"This link expires in {settings.reset_token_expire_minutes} minutes. "
        f"If you did not request this, you can safely ignore this email.",
    )


def send_invitation_email(to_email: str, full_name: str, set_password_token: str) -> None:
    link = f"{settings.frontend_base_url}/reset-password?token={set_password_token}"
    _send(
        to_email,
        "You've been added to CliniScribe AI",
        f"Hi {full_name},\n\n"
        f"An account has been created for you on CliniScribe AI. Set your "
        f"password to get started: {link}\n\n"
        f"This link expires in {settings.reset_token_expire_minutes} minutes.",
    )
