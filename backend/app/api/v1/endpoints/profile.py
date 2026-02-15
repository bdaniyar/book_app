from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.profile import ProfileUpdateRequest, ChangePasswordRequest
from app.schemas.user import UserRead
from app.services.users import get_user_by_email, get_user_by_username, change_password

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

    # username change (ensure unique)
    if payload.username is not None:
        new_username = payload.username.strip() or None
        if new_username != current_user.username:
            if new_username is not None:
                existing = get_user_by_username(db, new_username)
                if existing and existing.id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this username already exists",
                    )
            current_user.username = new_username

    if payload.first_name is not None:
        current_user.first_name = payload.first_name

    if payload.last_name is not None:
        current_user.last_name = payload.last_name

    if payload.bio is not None:
        current_user.bio = payload.bio

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    change_password(db, current_user, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
