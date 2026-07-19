import uuid
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session, sessionmaker
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import SessionLocal
from app.models.author import Author
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user import User
from app.models.user_book import UserBook
from app.services.users import get_user_by_email, get_user_by_username

ADMIN_USER_SESSION_KEY = "admin_user_id"
ADMIN_TOKEN_VERSION_SESSION_KEY = "admin_token_version"


class AdminAuthenticationBackend(AuthenticationBackend):
    """Signed-cookie SQLAdmin authentication backed by active superusers."""

    def __init__(
        self,
        secret_key: str,
        session_factory: sessionmaker[Session],
    ) -> None:
        # Build a dedicated, tightly scoped admin session cookie. SQLAdmin only
        # expects the ``middlewares`` attribute from its base implementation.
        self.middlewares = [
            Middleware(
                SessionMiddleware,
                secret_key=secret_key,
                session_cookie=settings.ADMIN_SESSION_COOKIE_NAME,
                max_age=settings.ADMIN_SESSION_MAX_AGE_SECONDS,
                path="/admin",
                same_site=settings.ADMIN_SESSION_COOKIE_SAMESITE,
                https_only=settings.ADMIN_SESSION_COOKIE_SECURE,
            )
        ]
        self.session_factory = session_factory

    @staticmethod
    def _same_origin(request: Request) -> bool:
        source = request.headers.get("origin") or request.headers.get("referer")
        if not source:
            # Non-browser clients may omit both. SameSite=Strict still protects
            # the browser session, while authentication remains mandatory.
            return True
        parsed = urlsplit(source)
        return parsed.netloc == request.headers.get("host")

    async def login(self, request: Request) -> bool:
        if not self._same_origin(request):
            return False

        form = await request.form()
        identifier = str(form.get("username") or "").strip()
        password = str(form.get("password") or "")
        if not identifier or not password:
            return False

        with self.session_factory() as db:
            if "@" in identifier:
                user = get_user_by_email(db, identifier)
            else:
                user = get_user_by_username(db, identifier)

            if not user or not user.is_active or not user.is_superuser:
                return False
            try:
                valid_password = verify_password(password, user.hashed_password)
            except (UnknownHashError, ValueError):
                return False
            if not valid_password:
                return False

            request.session.clear()
            request.session[ADMIN_USER_SESSION_KEY] = str(user.id)
            request.session[ADMIN_TOKEN_VERSION_SESSION_KEY] = user.token_version
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if request.method not in {"GET", "HEAD", "OPTIONS"} and not self._same_origin(
            request
        ):
            request.session.clear()
            return False

        raw_user_id = request.session.get(ADMIN_USER_SESSION_KEY)
        try:
            user_id = uuid.UUID(str(raw_user_id))
        except (TypeError, ValueError, AttributeError):
            request.session.clear()
            return False

        with self.session_factory() as db:
            user = db.get(User, user_id)
            session_token_version = request.session.get(
                ADMIN_TOKEN_VERSION_SESSION_KEY
            )
            if (
                not user
                or not user.is_active
                or not user.is_superuser
                or session_token_version != user.token_version
            ):
                request.session.clear()
                return False
            request.state.admin_user_id = user.id
            return True


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    column_list = [
        User.id,
        User.email,
        User.username,
        User.is_active,
        User.is_superuser,
        User.email_verified,
    ]
    column_searchable_list = [User.email, User.username]
    form_columns = [
        User.email,
        User.username,
        User.first_name,
        User.last_name,
        User.bio,
        User.avatar_url,
        User.is_active,
        User.is_superuser,
        User.email_verified,
    ]
    # Accounts and password hashes must be created through the auth service,
    # where validation and hashing cannot be bypassed.
    can_create = False
    can_delete = False

    async def on_model_change(self, data, model, is_created, request) -> None:
        if "email" in data and data["email"]:
            data["email"] = str(data["email"]).strip().lower()
        if "username" in data and data["username"]:
            data["username"] = str(data["username"]).strip()


class AuthorAdmin(ModelView, model=Author):
    column_list = [Author.id, Author.name]


class GenreAdmin(ModelView, model=Genre):
    column_list = [Genre.id, Genre.name]


class BookAdmin(ModelView, model=Book):
    column_list = [
        Book.id,
        Book.title,
        Book.author_id,
        Book.average_rating,
        Book.review_count,
    ]


class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.book_id, Review.user_id, Review.rating]


class UserBookAdmin(ModelView, model=UserBook):
    column_list = [UserBook.id, UserBook.user_id, UserBook.book_id, UserBook.status]


def configure_admin(
    app: FastAPI,
    *,
    session_factory: sessionmaker[Session] = SessionLocal,
) -> Admin:
    secret = settings.ADMIN_SESSION_SECRET_KEY
    if not secret or len(secret) < 32:
        raise RuntimeError(
            "ADMIN_SESSION_SECRET_KEY with at least 32 characters is required"
        )
    if secret == settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "ADMIN_SESSION_SECRET_KEY must be different from JWT_SECRET_KEY"
        )

    authentication_backend = AdminAuthenticationBackend(secret, session_factory)
    admin = Admin(
        app,
        session_maker=session_factory,
        authentication_backend=authentication_backend,
        title="Book App Admin",
    )
    admin.add_view(UserAdmin)
    admin.add_view(AuthorAdmin)
    admin.add_view(GenreAdmin)
    admin.add_view(BookAdmin)
    admin.add_view(ReviewAdmin)
    admin.add_view(UserBookAdmin)
    app.state.sqladmin = admin
    return admin
