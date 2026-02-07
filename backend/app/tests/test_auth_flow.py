import uuid


def test_register_sets_refresh_cookie_and_returns_access_token(client):
    payload = {
        "email": "alice@example.com",
        "password": "Str0ngPassw0rd!",
        "username": "alice",
    }

    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text

    body = r.json()
    assert "access_token" in body
    assert body.get("token_type", "bearer") in ("bearer", "Bearer")

    # refresh cookie should be set
    set_cookie = r.headers.get("set-cookie", "")
    assert "book_app_refresh=" in set_cookie
    assert "HttpOnly" in set_cookie


def test_login_refresh_me_logout_flow(client):
    # Register
    reg_payload = {
        "email": "bob@example.com",
        "password": "Str0ngPassw0rd!",
        "username": "bob",
    }
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 201, r.text
    access = r.json()["access_token"]

    # /me with access
    r_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r_me.status_code == 200, r_me.text
    me = r_me.json()
    assert me["email"] == reg_payload["email"]
    assert me.get("username") == reg_payload["username"]

    # refresh (cookie jar preserved by TestClient)
    r_ref = client.post("/api/v1/auth/refresh")
    assert r_ref.status_code == 200, r_ref.text
    new_access = r_ref.json()["access_token"]
    assert new_access

    # logout clears cookie
    r_lo = client.post("/api/v1/auth/logout")
    assert r_lo.status_code == 204
    set_cookie = r_lo.headers.get("set-cookie", "")
    assert "book_app_refresh=" in set_cookie


def test_register_username_conflict_returns_409(client):
    payload1 = {
        "email": "c1@example.com",
        "password": "Str0ngPassw0rd!",
        "username": "taken",
    }
    payload2 = {
        "email": "c2@example.com",
        "password": "Str0ngPassw0rd!",
        "username": "taken",
    }

    r1 = client.post("/api/v1/auth/register", json=payload1)
    assert r1.status_code == 201, r1.text

    r2 = client.post("/api/v1/auth/register", json=payload2)
    assert r2.status_code == 409, r2.text
