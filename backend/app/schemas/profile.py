from pydantic import BaseModel, EmailStr, Field


class ProfileUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    bio: str | None = Field(default=None, min_length=1, max_length=500)
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
    new_password2: str = Field(min_length=8)