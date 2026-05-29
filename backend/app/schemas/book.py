import uuid

from pydantic import BaseModel, Field


class BookRead(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    cover_url: str | None = Field(default=None, serialization_alias="coverUrl")
    rating: float
    review_count: int = Field(serialization_alias="reviewCount")
    description: str
    genre: str
    published_year: int | None = Field(default=None, serialization_alias="publishedYear")
    pages: int | None = None
    isbn: str | None = None

    model_config = {"populate_by_name": True}


class BookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    description: str = ""
    isbn: str | None = Field(default=None, max_length=32)
    cover_url: str | None = Field(default=None, max_length=2048)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=0, le=3000)
    genre_ids: list[uuid.UUID] = Field(default_factory=list)


class BookUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    isbn: str | None = Field(default=None, max_length=32)
    cover_url: str | None = Field(default=None, max_length=2048)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=0, le=3000)
    genre_ids: list[uuid.UUID] | None = None
