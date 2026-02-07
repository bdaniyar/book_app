from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from typing import cast, Literal

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, AccessTokenResponse
from app.schemas.user import UserRead
from app.services.users import create_user, get_user_by_email, get_user_by_username
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
from app.services.users import authenticate_user
from app.api.deps.auth import get_current_user
from app.core.config import settings
from app.core.jwt import decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=cast(
            Literal["lax", "strict", "none"], settings.REFRESH_COOKIE_SAMESITE
        ),
        path="/",
        max_age=int(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path="/")


@router.post(
    "/register", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest, response: Response, db: Session = Depends(get_db)
) -> AccessTokenResponse:
    existing = get_user_by_email(db, str(payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    if payload.username is not None:
        existing_username = get_user_by_username(db, payload.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists",
            )

    user = create_user(db, payload)

    subject = str(user.id)
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    _set_refresh_cookie(response, refresh)

    return AccessTokenResponse(access_token=access)


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> AccessTokenResponse:
    user = authenticate_user(db, str(payload.email), payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    subject = str(user.id)
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    _set_refresh_cookie(response, refresh)

    return AccessTokenResponse(access_token=access)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_access_token(request: Request, response: Response) -> AccessTokenResponse:
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Optionally rotate refresh token (simple rotation without server-side storage)
    new_refresh = create_refresh_token(str(subject))
    _set_refresh_cookie(response, new_refresh)

    return AccessTokenResponse(access_token=create_access_token(str(subject)))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
