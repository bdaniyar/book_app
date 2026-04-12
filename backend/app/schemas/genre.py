import uuid
from datetime import datetime

from pydantic import BaseModel


class GenreRead(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteGenresUpdateRequest(BaseModel):
    genre_ids: list[uuid.UUID]
