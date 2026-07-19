import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.user_book import ReadingStatus
from app.schemas.book import BookRead


class LibraryAddRequest(BaseModel):
    book_id: uuid.UUID = Field(validation_alias="bookId")
    status: ReadingStatus | None = None
    progress_pages: int | None = Field(default=None, validation_alias="progressPages", ge=0)
    is_favorite: bool | None = Field(default=None, validation_alias="isFavorite")

    model_config = {"populate_by_name": True}


class LibraryStatusUpdateRequest(BaseModel):
    status: ReadingStatus | None = None
    progress_pages: int | None = Field(default=None, validation_alias="progressPages", ge=0)
    is_favorite: bool | None = Field(default=None, validation_alias="isFavorite")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set or all(
            value is None
            for value in (self.status, self.progress_pages, self.is_favorite)
        ):
            raise ValueError("At least one library field must be provided")
        return self


class LibraryEntryRead(BaseModel):
    id: uuid.UUID
    book: BookRead
    status: ReadingStatus
    progress_pages: int = Field(serialization_alias="progressPages")
    is_favorite: bool = Field(serialization_alias="isFavorite")
    started_at: datetime | None = Field(serialization_alias="startedAt")
    finished_at: datetime | None = Field(serialization_alias="finishedAt")
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")

    model_config = {"populate_by_name": True}
