from __future__ import annotations

from pathlib import Path
from typing import cast
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from pydantic import SecretStr

from app.core.config import settings

# backend/app/templates
TEMPLATE_FOLDER = Path(__file__).resolve().parents[1] / "templates"


def get_mail_config() -> ConnectionConfig:
    if not settings.MAIL_USERNAME:
        raise RuntimeError("MAIL_USERNAME is not set")
    if not settings.MAIL_PASSWORD:
        raise RuntimeError("MAIL_PASSWORD is not set")
    if not settings.MAIL_FROM:
        raise RuntimeError("MAIL_FROM is not set")
    if not settings.MAIL_SERVER:
        raise RuntimeError("MAIL_SERVER is not set")

    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=TEMPLATE_FOLDER,
    )


async def send_text_email(*, to: str, subject: str, body: str) -> None:
    conf = get_mail_config()
    fm = FastMail(conf)

    message = MessageSchema(
        subject=subject,
        recipients=cast(list, [to]),
        body=body,
        subtype=MessageType.plain,
    )

    await fm.send_message(message)


async def send_password_reset_email(*, to: str, reset_link: str) -> None:
    conf = get_mail_config()
    fm = FastMail(conf)

    message = MessageSchema(
        subject="Reset your password",
        recipients=cast(list, [to]),
        body="",
        template_body={"reset_link": reset_link},
        subtype=MessageType.html,
    )

    # Template path is relative to backend/app/
    await fm.send_message(message, template_name="password_reset.html")

