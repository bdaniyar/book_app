import uuid

from pydantic import BaseModel, Field

from app.models.user_book import ReadingStatus


class LibraryAddRequest(BaseModel):
    book_id: uuid.UUID = Field(validation_alias="bookId")
    status: ReadingStatus

    model_config = {"populate_by_name": True}


class LibraryStatusUpdateRequest(BaseModel):
    status: ReadingStatus
    progress_pages: int | None = Field(default=None, validation_alias="progressPages", ge=0)

    model_config = {"populate_by_name": True}
