from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None:  # pragma: no cover
        """Send an email message."""


class ConsoleEmailSender:
    """Dev-only sender that prints emails to stdout."""

    def send(self, message: EmailMessage) -> None:
        print("[DEV EMAIL]")
        print(f"To: {message.to}")
        print(f"Subject: {message.subject}")
        print(message.text)


class SmtpEmailSender:
    """SMTP sender scaffold (credentials provided via settings).

    Notes:
    - Uses STARTTLS.
    - No secrets embedded in code.
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    def send(self, message: EmailMessage) -> None:
        import smtplib
        from email.message import EmailMessage as _EmailMessage

        em = _EmailMessage()
        em["From"] = self.from_email
        em["To"] = message.to
        em["Subject"] = message.subject
        em.set_content(message.text)
        if message.html:
            em.add_alternative(message.html, subtype="html")

        with smtplib.SMTP(self.host, self.port) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password)
            smtp.send_message(em)


def build_email_sender(
    *,
    provider: str,
    dev_output: bool,
    smtp_host: str | None,
    smtp_port: int,
    smtp_username: str | None,
    smtp_password: str | None,
    from_email: str | None,
) -> EmailSender:
    if dev_output:
        return ConsoleEmailSender()

    if provider.lower() == "smtp":
        if not (smtp_host and from_email and smtp_username and smtp_password):
            raise RuntimeError(
                "SMTP email provider is selected but SMTP settings are missing"
            )
        return SmtpEmailSender(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            from_email=from_email,
        )

    raise RuntimeError(f"Unsupported EMAIL_PROVIDER: {provider}")
