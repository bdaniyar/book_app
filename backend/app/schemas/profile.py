import unicodedata

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.auth import _normalize_email, _normalize_username


def _normalize_optional_text(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFKC", value).strip()
    return value


class ProfileUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=320)
    bio: str | None = Field(default=None, min_length=1, max_length=500)
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)

    _email_normalizer = field_validator("email", mode="before")(_normalize_email)
    _username_normalizer = field_validator("username", mode="before")(
        _normalize_username
    )
    _text_normalizer = field_validator(
        "bio", "first_name", "last_name", mode="before"
    )(_normalize_optional_text)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
    new_password2: str = Field(min_length=8, max_length=72)
