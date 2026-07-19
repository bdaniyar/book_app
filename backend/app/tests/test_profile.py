def _register_and_get_access(client, *, email: str, username: str) -> str:
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!", "username": username},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def test_get_profile_requires_auth(client):
    r = client.get("/api/v1/profile")
    assert r.status_code in (401, 403)


def test_get_and_update_profile(client):
    access = _register_and_get_access(client, email="p1@example.com", username="p1")

    r = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "p1@example.com"
    assert body.get("username") == "p1"

    upd = {
        "first_name": "Alice",
        "last_name": "Reader",
        "bio": "Hello!",
        "email": "p1-new@example.com",
        "username": "p1_new",
    }
    r2 = client.put(
        "/api/v1/profile",
        json=upd,
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["email"] == "p1-new@example.com"
    assert body2.get("username") == "p1_new"
    assert body2.get("first_name") == "Alice"
    assert body2.get("last_name") == "Reader"
    assert body2.get("bio") == "Hello!"


def test_profile_update_conflicts(client):
    access1 = _register_and_get_access(client, email="p2a@example.com", username="p2a")
    _register_and_get_access(client, email="p2b@example.com", username="p2b")

    # username conflict
    r = client.put(
        "/api/v1/profile",
        json={"username": "p2b"},
        headers={"Authorization": f"Bearer {access1}"},
    )
    assert r.status_code == 409, r.text

    # email conflict
    r2 = client.put(
        "/api/v1/profile",
        json={"email": "p2b@example.com"},
        headers={"Authorization": f"Bearer {access1}"},
    )
    assert r2.status_code == 409, r2.text


def test_profile_patch_can_clear_optional_fields_but_not_email(client):
    access = _register_and_get_access(
        client, email="clear@example.com", username="clear_me"
    )
    headers = {"Authorization": f"Bearer {access}"}

    populated = client.patch(
        "/api/v1/profile",
        json={"first_name": "Alice", "bio": "Temporary"},
        headers=headers,
    )
    assert populated.status_code == 200, populated.text

    cleared = client.patch(
        "/api/v1/profile",
        json={"username": None, "first_name": None, "bio": None},
        headers=headers,
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["username"] is None
    assert cleared.json()["first_name"] is None
    assert cleared.json()["bio"] is None

    invalid_email = client.patch(
        "/api/v1/profile", json={"email": None}, headers=headers
    )
    assert invalid_email.status_code == 422


def test_change_password_flow(client):
    access = _register_and_get_access(client, email="pw1@example.com", username="pw1")

    # wrong current password
    r_bad = client.put(
        "/api/v1/profile/password",
        json={
            "current_password": "wrongpass123",
            "new_password": "NewPassw0rd!",
            "new_password2": "NewPassw0rd!",
        },
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r_bad.status_code == 400, r_bad.text

    # correct current password
    r_ok = client.put(
        "/api/v1/profile/password",
        json={
            "current_password": "Str0ngPassw0rd!",
            "new_password": "NewPassw0rd!",
            "new_password2": "NewPassw0rd!",
        },
        headers={"Authorization": f"Bearer {access}"},
    )
    assert r_ok.status_code == 204, r_ok.text

    # login with new password should work
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "pw1@example.com", "password": "NewPassw0rd!"},
    )
    assert r_login.status_code == 200, r_login.text
