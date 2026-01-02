from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Must be provided via environment or backend/.env
    DATABASE_URL: str | None = None

    # JWT
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Put it into backend/.env")

if not settings.JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set. Put it into backend/.env")
