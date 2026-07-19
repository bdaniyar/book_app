import unicodedata

from pydantic import BaseModel, EmailStr, Field, field_validator


def _normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _normalize_username(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFKC", value).strip()
    return value


class RegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8, max_length=72)
    username: str = Field(min_length=1, max_length=100)

    _email_normalizer = field_validator("email", mode="before")(_normalize_email)
    _username_normalizer = field_validator("username", mode="before")(
        _normalize_username
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=8, max_length=72)

    _email_normalizer = field_validator("email", mode="before")(_normalize_email)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=320)

    _email_normalizer = field_validator("email", mode="before")(_normalize_email)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=4096)
    new_password: str = Field(min_length=8, max_length=72)
    new_password2: str = Field(min_length=8, max_length=72)


class TokenRequest(BaseModel):
    token: str = Field(min_length=10, max_length=4096)
