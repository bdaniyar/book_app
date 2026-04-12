import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.genre import Genre
from app.schemas.genre import GenreRead

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=list[GenreRead])
def list_genres(db: Session = Depends(get_db)) -> list[Genre]:
    return db.query(Genre).order_by(Genre.name.asc()).all()


@router.post("", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(name: str, db: Session = Depends(get_db)) -> Genre:
    # Minimal admin-ish endpoint for now; can be locked down later.
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")

    existing = db.query(Genre).filter(Genre.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Genre already exists")

    g = Genre(name=name)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/{genre_id}", response_model=GenreRead)
def get_genre(genre_id: uuid.UUID, db: Session = Depends(get_db)) -> Genre:
    g = db.query(Genre).filter(Genre.id == genre_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Genre not found")
    return g
