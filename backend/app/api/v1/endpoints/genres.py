import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.genre import Genre
from app.models.user import User
from app.api.deps.auth import get_current_superuser
from app.schemas.genre import GenreRead

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreRead])
def list_genres(db: Session = Depends(get_db)) -> list[Genre]:
    return db.query(Genre).order_by(Genre.name.asc()).all()


@router.post("", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(
    name: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> Genre:
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    if len(name) > 100:
        raise HTTPException(status_code=422, detail="Name is too long")

    existing = db.query(Genre).filter(Genre.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Genre already exists")

    g = Genre(name=name)
    db.add(g)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Genre already exists") from None
    db.refresh(g)
    return g


@router.get("/{genre_id}", response_model=GenreRead)
def get_genre(genre_id: uuid.UUID, db: Session = Depends(get_db)) -> Genre:
    g = db.query(Genre).filter(Genre.id == genre_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Genre not found")
    return g
