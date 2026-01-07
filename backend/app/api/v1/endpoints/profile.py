from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileUpdateRequest
from app.schemas.user import UserRead
from app.services.users import get_user_by_email

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserRead)
def get_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("", response_model=UserRead)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    # email change (ensure unique)
    if payload.email is not None:
        new_email = str(payload.email)
        if new_email != current_user.email:
            existing = get_user_by_email(db, new_email)
            if existing and existing.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )
            current_user.email = new_email

    # name change
    if payload.name is not None:
        current_user.name = payload.name

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
