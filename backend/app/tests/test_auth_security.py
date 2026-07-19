import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.admin.admin import configure_admin
from app.core.config import Settings, settings
from app.core.security import create_password_reset_token
from app.models.user import User
from app.services.tokens import store_password_reset_token


PASSWORD = "Str0ngPassw0rd!"
NEW_PASSWORD = "An0therStr0ngPass!"


def test_configuration_rejects_insecure_production_values():
    production = {
        "APP_ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+psycopg://example/test",
        "JWT_SECRET_KEY": "s" * 64,
        "REFRESH_COOKIE_SECURE": True,
        "FRONTEND_ORIGINS": "https://books.example.com",
        "FRONTEND_RESET_PASSWORD_URL": (
            "https://books.example.com/reset-password"
        ),
    }
    assert Settings(**production).APP_ENVIRONMENT == "production"

    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(**{**production, "JWT_SECRET_KEY": "too-short"})
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(
            **{
                **production,
                "FRONTEND_ORIGINS": "http://books.example.com",
            }
        )
    with pytest.raises(ValidationError, match="Wildcard"):
        Settings(
            DATABASE_URL="postgresql+psycopg://example/test",
            JWT_SECRET_KEY="s" * 64,
            FRONTEND_ORIGINS="*",
        )


def _register(client, *, email: str, username: str):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "username": username},
    )
    assert response.status_code == 201, response.text
    return response


def test_malformed_jwts_return_controlled_client_errors(client):
    malformed = "this-is-not-a-valid-jwt"

    client.cookies.set(settings.REFRESH_COOKIE_NAME, malformed)
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401
    assert refresh.json()["detail"] == "Invalid refresh token"

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": malformed,
            "new_password": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
    )
    assert reset.status_code == 400
    assert reset.json()["detail"] == "Invalid reset token"

    verification = client.post(
        "/api/v1/auth/verify-email", json={"token": malformed}
    )
    assert verification.status_code == 400
    assert verification.json()["detail"] == "Invalid verification token"


def test_inactive_user_cannot_login_use_access_or_refresh(client, db_session):
    registration = _register(
        client, email="inactive@example.com", username="inactive_user"
    )
    access_token = registration.json()["access_token"]
    refresh_token = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    user = db_session.scalar(
        select(User).where(User.email == "inactive@example.com")
    )
    assert user is not None
    user.is_active = False
    db_session.commit()

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 403
    assert me.json()["detail"] == "Inactive user"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": PASSWORD},
    )
    assert login.status_code == 401

    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401


def test_refresh_rotation_consumes_the_previous_token_once(client):
    _register(client, email="rotate@example.com", username="rotate_user")
    previous_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    first = client.post("/api/v1/auth/refresh")
    assert first.status_code == 200, first.text
    assert client.cookies.get(settings.REFRESH_COOKIE_NAME) != previous_refresh

    client.cookies.set(settings.REFRESH_COOKIE_NAME, previous_refresh)
    replay = client.post("/api/v1/auth/refresh")
    assert replay.status_code == 401


def test_password_change_revokes_existing_refresh_sessions(client):
    registration = _register(
        client, email="password-change@example.com", username="password_change"
    )
    access_token = registration.json()["access_token"]
    previous_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    changed = client.put(
        "/api/v1/profile/password",
        json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
            "new_password2": NEW_PASSWORD,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert changed.status_code == 204, changed.text

    old_access = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert old_access.status_code == 401

    client.cookies.set(settings.REFRESH_COOKIE_NAME, previous_refresh)
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401


def test_password_reset_is_one_time_and_revokes_refresh_sessions(
    client, db_session
):
    registration = _register(
        client, email="password-reset@example.com", username="password_reset"
    )
    old_access_token = registration.json()["access_token"]
    previous_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    user = db_session.scalar(
        select(User).where(User.email == "password-reset@example.com")
    )
    assert user is not None

    reset_token = create_password_reset_token(str(user.id))
    store_password_reset_token(db_session, user.id, reset_token)
    payload = {
        "token": reset_token,
        "new_password": NEW_PASSWORD,
        "new_password2": NEW_PASSWORD,
    }

    reset = client.post("/api/v1/auth/reset-password", json=payload)
    assert reset.status_code == 204, reset.text
    assert "Max-Age=0" in reset.headers.get("set-cookie", "")

    old_access = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {old_access_token}"},
    )
    assert old_access.status_code == 401

    replay = client.post("/api/v1/auth/reset-password", json=payload)
    assert replay.status_code == 400

    client.cookies.set(settings.REFRESH_COOKIE_NAME, previous_refresh)
    refresh = client.post("/api/v1/auth/refresh")
    assert refresh.status_code == 401

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "password-reset@example.com", "password": PASSWORD},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "password-reset@example.com", "password": NEW_PASSWORD},
    )
    assert new_login.status_code == 200


def test_registration_normalizes_identity_and_matches_database_limits(client):
    registration = _register(
        client,
        email="  Normalized.User@Example.COM ",
        username="  normalized_user  ",
    )
    access_token = registration.json()["access_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "normalized.user@example.com"
    assert me.json()["username"] == "normalized_user"

    duplicate_case_variant = client.post(
        "/api/v1/auth/register",
        json={
            "email": "NORMALIZED.USER@example.com",
            "password": PASSWORD,
            "username": "another_username",
        },
    )
    assert duplicate_case_variant.status_code == 409

    blank_username = client.post(
        "/api/v1/auth/register",
        json={
            "email": "blank@example.com",
            "password": PASSWORD,
            "username": "   ",
        },
    )
    assert blank_username.status_code == 422

    too_long_username = client.post(
        "/api/v1/auth/register",
        json={
            "email": "long@example.com",
            "password": PASSWORD,
            "username": "u" * 101,
        },
    )
    assert too_long_username.status_code == 422


def test_admin_is_disabled_by_default(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code == 404


def test_admin_requires_an_active_superuser_session(
    client, db_session, monkeypatch
):
    _register(client, email="admin@example.com", username="admin_user")
    user = db_session.scalar(select(User).where(User.email == "admin@example.com"))
    assert user is not None

    admin_session_factory = sessionmaker(
        bind=db_session.connection(),
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    monkeypatch.setattr(settings, "ADMIN_SESSION_SECRET_KEY", "a" * 64)
    configure_admin(client.app, session_factory=admin_session_factory)

    anonymous = client.get("/admin/", follow_redirects=False)
    assert anonymous.status_code == 302
    assert anonymous.headers["location"].endswith("/admin/login")

    regular_user = client.post(
        "/admin/login",
        data={"username": "admin@example.com", "password": PASSWORD},
        follow_redirects=False,
    )
    assert regular_user.status_code == 400

    user.is_superuser = True
    db_session.commit()
    authenticated = client.post(
        "/admin/login",
        data={"username": "admin@example.com", "password": PASSWORD},
        follow_redirects=False,
    )
    assert authenticated.status_code == 302
    assert settings.ADMIN_SESSION_COOKIE_NAME in authenticated.headers.get(
        "set-cookie", ""
    )

    dashboard = client.get("/admin/", follow_redirects=False)
    assert dashboard.status_code == 200

    user.is_active = False
    db_session.commit()
    deactivated = client.get("/admin/", follow_redirects=False)
    assert deactivated.status_code == 302
    assert deactivated.headers["location"].endswith("/admin/login")


def test_health_endpoints_and_security_headers(client):
    live = client.get("/health/live", headers={"X-Request-ID": "test-request-1"})
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    assert live.headers["x-request-id"] == "test-request-1"
    assert live.headers["x-content-type-options"] == "nosniff"
    assert live.headers["x-frame-options"] == "DENY"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}
