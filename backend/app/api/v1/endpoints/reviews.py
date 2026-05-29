import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.book import Book
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreateRequest, ReviewRead, ReviewUpdateRequest
from app.services.books import recalculate_book_rating

router = APIRouter(prefix="/reviews", tags=["reviews"])


def review_to_read(review: Review) -> ReviewRead:
    name = review.user.username or review.user.email
    return ReviewRead(
        id=review.id,
        book_id=review.book_id,
        user_id=review.user_id,
        user_name=name,
        user_avatar=review.user.avatar_url,
        rating=review.rating,
        text=review.text,
        created_at=review.created_at,
        helpful=review.helpful,
    )


@router.get("/book/{book_id}", response_model=list[ReviewRead])
def list_reviews(
    book_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ReviewRead]:
    reviews = db.scalars(
        select(Review)
        .options(selectinload(Review.user))
        .where(Review.book_id == book_id)
        .order_by(Review.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    return [review_to_read(review) for review in reviews]


@router.post("", response_model=ReviewRead, status_code=201)
def create_review(
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewRead:
    if not db.get(Book, payload.book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    review = Review(
        book_id=payload.book_id,
        user_id=current_user.id,
        rating=payload.rating,
        text=payload.text,
    )
    db.add(review)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="You already reviewed this book")
    recalculate_book_rating(db, payload.book_id)
    db.commit()
    db.refresh(review)
    return review_to_read(review)


@router.put("/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: uuid.UUID,
    payload: ReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewRead:
    review = db.scalar(
        select(Review).options(selectinload(Review.user)).where(Review.id == review_id)
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot edit this review")
    review.rating = payload.rating
    review.text = payload.text
    db.add(review)
    recalculate_book_rating(db, review.book_id)
    db.commit()
    db.refresh(review)
    return review_to_read(review)


@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    review = db.get(Review, review_id)
    if not review:
        return None
    if review.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot delete this review")
    book_id = review.book_id
    db.delete(review)
    db.flush()
    recalculate_book_rating(db, book_id)
    db.commit()
    return None
