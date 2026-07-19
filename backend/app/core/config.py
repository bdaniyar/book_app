import os
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENVIRONMENT: Literal["development", "test", "staging", "production"] = (
        "development"
    )

    # Must be provided via environment or backend/.env
    DATABASE_URL: str | None = None

    # JWT
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Auth cookies
    REFRESH_COOKIE_NAME: str = "book_app_refresh"
    REFRESH_COOKIE_SECURE: bool = False  # set True in production (https)
    REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # SQLAdmin is opt-in and uses a separate signed session cookie. Never reuse
    # JWT_SECRET_KEY here: compromising one credential must not compromise both
    # user JWTs and administrator sessions.
    ADMIN_ENABLED: bool = False
    ADMIN_SESSION_SECRET_KEY: str | None = None
    ADMIN_SESSION_COOKIE_NAME: str = "book_app_admin_session"
    ADMIN_SESSION_COOKIE_SECURE: bool = False
    ADMIN_SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "strict"
    ADMIN_SESSION_MAX_AGE_SECONDS: int = 8 * 60 * 60

    # Grounded reading assistant. The local provider works without credentials;
    # hosted model calls are made only from the backend.
    AI_PROVIDER: Literal["local", "openai"] = "local"
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL: str = "gpt-5.6-sol"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1, le=120)
    AI_MAX_OUTPUT_TOKENS: int = Field(default=900, ge=100, le=4000)

    # Password reset (forgot password)
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_RESET_PASSWORD_URL: str = "http://localhost:3000/reset-password"
    DEV_EMAIL_OUTPUT: bool = (
        False # in dev: print reset link to logs instead of sending email
    )

    # Email provider (scaffold)
    EMAIL_PROVIDER: str = "smtp"  # currently supported: 'smtp'
    EMAIL_FROM: str | None = None

    # CORS
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

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

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        origins = [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ]
        if "*" in origins:
            raise ValueError(
                "Wildcard FRONTEND_ORIGINS is not allowed with credentialed CORS"
            )

        if self.REFRESH_COOKIE_SAMESITE == "none" and not self.REFRESH_COOKIE_SECURE:
            raise ValueError(
                "REFRESH_COOKIE_SECURE must be true when SameSite is 'none'"
            )

        if self.ADMIN_ENABLED:
            secret = self.ADMIN_SESSION_SECRET_KEY or ""
            if len(secret) < 32:
                raise ValueError(
                    "ADMIN_SESSION_SECRET_KEY must contain at least 32 characters "
                    "when ADMIN_ENABLED is true"
                )
            if secret == self.JWT_SECRET_KEY:
                raise ValueError(
                    "ADMIN_SESSION_SECRET_KEY must be different from JWT_SECRET_KEY"
                )
            if (
                self.ADMIN_SESSION_COOKIE_SAMESITE == "none"
                and not self.ADMIN_SESSION_COOKIE_SECURE
            ):
                raise ValueError(
                    "ADMIN_SESSION_COOKIE_SECURE must be true when admin SameSite "
                    "is 'none'"
                )

        if self.APP_ENVIRONMENT == "production":
            if len(self.JWT_SECRET_KEY or "") < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must contain at least 32 characters in production"
                )
            if not self.REFRESH_COOKIE_SECURE:
                raise ValueError(
                    "REFRESH_COOKIE_SECURE must be true in production"
                )
            if self.ADMIN_ENABLED and not self.ADMIN_SESSION_COOKIE_SECURE:
                raise ValueError(
                    "ADMIN_SESSION_COOKIE_SECURE must be true in production"
                )
            if self.DEV_EMAIL_OUTPUT:
                raise ValueError("DEV_EMAIL_OUTPUT must be false in production")
            if any(not origin.startswith("https://") for origin in origins):
                raise ValueError(
                    "Every production FRONTEND_ORIGINS entry must use HTTPS"
                )
            if not self.FRONTEND_RESET_PASSWORD_URL.startswith("https://"):
                raise ValueError(
                    "FRONTEND_RESET_PASSWORD_URL must use HTTPS in production"
                )

        if self.AI_PROVIDER == "openai" and self.OPENAI_API_KEY is None:
            raise ValueError(
                "OPENAI_API_KEY is required when AI_PROVIDER is 'openai'"
            )

        return self


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it into backend/.env")

if not settings.JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set. Put it into backend/.env")
