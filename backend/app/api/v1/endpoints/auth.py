from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from typing import cast, Literal

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    AccessTokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenRequest,
)
from app.schemas.user import UserRead
from app.services.users import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
)
from app.models.user import User
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    create_email_verification_token,
    hash_password,
)
from app.services.users import authenticate_user
from app.api.deps.auth import get_current_user
from app.core.config import settings
from app.core.jwt import decode_token
from app.services.email import EmailMessage, build_email_sender
from app.services.mail import send_password_reset_email
from app.services.tokens import (
    get_active_refresh_token,
    get_usable_email_verification_token,
    get_usable_password_reset_token,
    mark_email_verification_used,
    mark_password_reset_used,
    revoke_refresh_token,
    store_email_verification_token,
    store_password_reset_token,
    store_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_RATE_LIMITS: dict[tuple[str, str], list[datetime]] = {}


def _rate_limit(request: Request, key: str, *, limit: int, window_seconds: int) -> None:
    client = request.client.host if request.client else "unknown"
    bucket = (key, client)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=window_seconds)
    events = [ts for ts in _RATE_LIMITS.get(bucket, []) if ts > window_start]
    if len(events) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please try again later",
        )
    events.append(now)
    _RATE_LIMITS[bucket] = events


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
    store_refresh_token(db, user.id, refresh)
    _set_refresh_cookie(response, refresh)

    verification = create_email_verification_token(subject)
    store_email_verification_token(db, user.id, verification)

    return AccessTokenResponse(access_token=access)


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> AccessTokenResponse:
    _rate_limit(request, "login", limit=10, window_seconds=60)
    user = authenticate_user(db, str(payload.email), payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    subject = str(user.id)
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    store_refresh_token(db, user.id, refresh)
    _set_refresh_cookie(response, refresh)

    return AccessTokenResponse(access_token=access)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_access_token(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> AccessTokenResponse:
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

    active = get_active_refresh_token(db, refresh_token)
    if not active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    revoke_refresh_token(db, refresh_token)
    new_refresh = create_refresh_token(str(subject))
    store_refresh_token(db, active.user_id, new_refresh)
    _set_refresh_cookie(response, new_refresh)

    return AccessTokenResponse(access_token=create_access_token(str(subject)))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> Response:
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    _rate_limit(request, "forgot-password", limit=5, window_seconds=300)
    # Always return 204 to avoid leaking whether user exists.
    user = get_user_by_email(db, str(payload.email))
    if user:
        token = create_password_reset_token(str(user.id))
        store_password_reset_token(db, user.id, token)
        reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={token}"

        subject = "Reset your password"
        body = (
            "You requested a password reset.\n\n"
            f"Reset link: {reset_link}\n\n"
            "If you did not request this, you can ignore this email."
        )

        if settings.DEV_EMAIL_OUTPUT:
            sender = build_email_sender(
                provider=settings.EMAIL_PROVIDER,
                dev_output=True,
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT,
                smtp_username=settings.SMTP_USERNAME,
                smtp_password=settings.SMTP_PASSWORD,
                from_email=settings.EMAIL_FROM,
            )
            sender.send(EmailMessage(to=str(user.email), subject=subject, text=body))
        else:
            import asyncio

            asyncio.run(send_password_reset_email(to=str(user.email), reset_link=reset_link))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> Response:
    if payload.new_password != payload.new_password2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    token_payload = decode_token(payload.token)
    if token_payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    subject = token_payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    try:
        import uuid as _uuid

        user_id = _uuid.UUID(str(subject))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    reset_row = get_usable_password_reset_token(db, payload.token)
    if not reset_row or reset_row.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user.hashed_password = hash_password(payload.new_password)
    mark_password_reset_used(db, reset_row)
    db.add(user)
    db.commit()
    db.refresh(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: TokenRequest, db: Session = Depends(get_db)) -> Response:
    token_payload = decode_token(payload.token)
    if token_payload.get("type") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid verification token")
    subject = token_payload.get("sub")
    if not subject:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    try:
        import uuid as _uuid

        user_id = _uuid.UUID(str(subject))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user = get_user_by_id(db, user_id)
    token_row = get_usable_email_verification_token(db, payload.token)
    if not user or not token_row or token_row.user_id != user.id:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user.email_verified = True
    mark_email_verification_used(db, token_row)
    db.add(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
