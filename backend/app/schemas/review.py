import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewRead(BaseModel):
    id: uuid.UUID
    book_id: uuid.UUID = Field(serialization_alias="bookId")
    user_id: uuid.UUID = Field(serialization_alias="userId")
    user_name: str = Field(serialization_alias="userName")
    user_avatar: str | None = Field(default=None, serialization_alias="userAvatar")
    rating: int
    text: str
    created_at: datetime = Field(serialization_alias="createdAt")
    helpful: int

    model_config = {"populate_by_name": True}


class ReviewCreateRequest(BaseModel):
    book_id: uuid.UUID = Field(validation_alias="bookId")
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=5000)

    model_config = {"populate_by_name": True}


class ReviewUpdateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1, max_length=5000)
