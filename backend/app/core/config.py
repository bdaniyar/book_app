from pydantic_settings import BaseSettings, SettingsConfigDict

import os


class Settings(BaseSettings):
    # Must be provided via environment or backend/.env
    DATABASE_URL: str | None = None

    # JWT
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Auth cookies
    REFRESH_COOKIE_NAME: str = "book_app_refresh"
    REFRESH_COOKIE_SECURE: bool = False  # set True in production (https)
    REFRESH_COOKIE_SAMESITE: str = "lax"  # 'lax' works well for local dev

    # Password reset (forgot password)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password"
    DEV_EMAIL_OUTPUT: bool = (
        False # in dev: print reset link to logs instead of sending email
    )

    # Email provider (scaffold)
    EMAIL_PROVIDER: str = "smtp"  # currently supported: 'smtp'
    EMAIL_FROM: str | None = None

    # SMTP settings (can be SendPulse SMTP or any provider)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None

    # FastAPI-Mail (Gmail SMTP)
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str | None = None
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it into backend/.env")

if not settings.JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set. Put it into backend/.env")
