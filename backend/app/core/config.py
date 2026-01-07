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
