import uuid

from pydantic import BaseModel, Field, field_validator


def _clean_required_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Value must not be blank")
    return cleaned


class BookRead(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    cover_url: str | None = Field(default=None, serialization_alias="coverUrl")
    rating: float
    review_count: int = Field(serialization_alias="reviewCount")
    external_rating: float = Field(serialization_alias="externalRating")
    external_review_count: int = Field(serialization_alias="externalReviewCount")
    local_rating: float = Field(serialization_alias="localRating")
    local_review_count: int = Field(serialization_alias="localReviewCount")
    description: str
    genre: str
    genres: list[str]
    published_year: int | None = Field(default=None, serialization_alias="publishedYear")
    pages: int | None = None
    isbn: str | None = None
    external_source: str | None = Field(default=None, serialization_alias="externalSource")
    external_id: str | None = Field(default=None, serialization_alias="externalId")
    recommendation_reason: str | None = Field(
        default=None, serialization_alias="recommendationReason"
    )

    model_config = {"populate_by_name": True}


class BookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    description: str = ""
    isbn: str | None = Field(default=None, max_length=32)
    external_source: str | None = Field(default=None, max_length=64)
    external_id: str | None = Field(default=None, max_length=128)
    cover_url: str | None = Field(default=None, max_length=2048)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=0, le=3000)
    genre_ids: list[uuid.UUID] = Field(default_factory=list)

    _clean_title_author = field_validator("title", "author")(
        _clean_required_text
    )


class BookUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    isbn: str | None = Field(default=None, max_length=32)
    external_source: str | None = Field(default=None, max_length=64)
    external_id: str | None = Field(default=None, max_length=128)
    cover_url: str | None = Field(default=None, max_length=2048)
    pages: int | None = Field(default=None, ge=1)
    published_year: int | None = Field(default=None, ge=0, le=3000)
    genre_ids: list[uuid.UUID] | None = None

    @field_validator("title", "author")
    @classmethod
    def clean_optional_required_text(cls, value: str | None) -> str | None:
        return _clean_required_text(value) if value is not None else None
