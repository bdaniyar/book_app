import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from app.core.jwt import JWTError, decode_token
from app.services.email import EmailMessage, build_email_sender
from app.services.mail import send_password_reset_email
from app.services.tokens import (
    get_usable_email_verification_token,
    get_usable_password_reset_token,
    mark_email_verification_used,
    mark_password_reset_used,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    store_email_verification_token,
    store_password_reset_token,
    store_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

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
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/",
        max_age=int(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/",
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def _decode_subject(
    token: str,
    *,
    expected_type: str,
    invalid_status: int,
    detail: str,
) -> uuid.UUID:
    try:
        token_payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=invalid_status, detail=detail) from None

    if token_payload.get("type") != expected_type:
        raise HTTPException(status_code=invalid_status, detail=detail)

    subject = token_payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=invalid_status, detail=detail)

    try:
        return uuid.UUID(subject)
    except (TypeError, ValueError, AttributeError):
        raise HTTPException(status_code=invalid_status, detail=detail) from None


def _send_password_reset_message(*, to: str, reset_link: str) -> None:
    """Best-effort background delivery that never changes the public response."""

    try:
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
            sender.send(
                EmailMessage(
                    to=to,
                    subject="Reset your password",
                    text=(
                        "You requested a password reset.\n\n"
                        f"Reset link: {reset_link}\n\n"
                        "If you did not request this, you can ignore this email."
                    ),
                )
            )
        else:
            asyncio.run(send_password_reset_email(to=to, reset_link=reset_link))
    except Exception:
        # Do not leak account existence or mail-provider failures to callers.
        logger.exception("Password reset email delivery failed")


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

    try:
        user = create_user(db, payload, commit=False)
        subject = str(user.id)
        access = create_access_token(
            subject, token_version=user.token_version
        )
        refresh = create_refresh_token(subject)
        verification = create_email_verification_token(subject)
        store_refresh_token(db, user.id, refresh, commit=False)
        store_email_verification_token(db, user.id, verification, commit=False)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        ) from None
    except Exception:
        db.rollback()
        raise

    _set_refresh_cookie(response, refresh)

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
    access = create_access_token(subject, token_version=user.token_version)
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

    user_id = _decode_subject(
        refresh_token,
        expected_type="refresh",
        invalid_status=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    subject = str(user_id)
    new_refresh = create_refresh_token(subject)
    replacement = rotate_refresh_token(
        db,
        refresh_token,
        new_refresh,
        expected_user_id=user_id,
    )
    if not replacement:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    _set_refresh_cookie(response, new_refresh)

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    return AccessTokenResponse(
        access_token=create_access_token(
            subject, token_version=user.token_version
        )
    )


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Response:
    _rate_limit(request, "forgot-password", limit=5, window_seconds=300)
    # Always return 204 to avoid leaking whether user exists.
    user = get_user_by_email(db, str(payload.email))
    if user:
        token = create_password_reset_token(str(user.id))
        store_password_reset_token(db, user.id, token)
        reset_link = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={token}"

        background_tasks.add_task(
            _send_password_reset_message,
            to=str(user.email),
            reset_link=reset_link,
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    if payload.new_password != payload.new_password2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    user_id = _decode_subject(
        payload.token,
        expected_type="password_reset",
        invalid_status=status.HTTP_400_BAD_REQUEST,
        detail="Invalid reset token",
    )

    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    reset_row = get_usable_password_reset_token(
        db, payload.token, for_update=True
    )
    if not reset_row or reset_row.user_id != user.id:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user.hashed_password = hash_password(payload.new_password)
    user.token_version += 1
    mark_password_reset_used(db, reset_row)
    db.add(user)
    revoke_all_refresh_tokens(db, user.id, commit=False)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(user)
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(payload: TokenRequest, db: Session = Depends(get_db)) -> Response:
    user_id = _decode_subject(
        payload.token,
        expected_type="email_verification",
        invalid_status=status.HTTP_400_BAD_REQUEST,
        detail="Invalid verification token",
    )
    user = get_user_by_id(db, user_id)
    token_row = get_usable_email_verification_token(
        db, payload.token, for_update=True
    )
    if not user or not token_row or token_row.user_id != user.id:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user.email_verified = True
    mark_email_verification_used(db, token_row)
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)
