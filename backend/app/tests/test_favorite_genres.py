import uuid


def test_favorite_genres_crud(client, db_session):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fav@example.com",
            "password": "Str0ngPassw0rd!",
            "username": "fav",
        },
    )
    assert reg.status_code == 201, reg.text
    access = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    # Seed genres
    from app.models.genre import Genre

    g1 = Genre(name="Fiction")
    g2 = Genre(name="Mystery")
    db_session.add_all([g1, g2])
    db_session.commit()
    db_session.refresh(g1)
    db_session.refresh(g2)

    # Initially empty
    r = client.get("/api/v1/profile/favorite-genres", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    # Add one
    r = client.post(f"/api/v1/profile/favorite-genres/{g1.id}", headers=headers)
    assert r.status_code == 200
    assert {x["id"] for x in r.json()} == {str(g1.id)}

    # Replace list
    r = client.put(
        "/api/v1/profile/favorite-genres",
        headers=headers,
        json={"genre_ids": [str(g2.id)]},
    )
    assert r.status_code == 200
    assert {x["id"] for x in r.json()} == {str(g2.id)}

    # Remove
    r = client.delete(f"/api/v1/profile/favorite-genres/{g2.id}", headers=headers)
    assert r.status_code == 200
    assert r.json() == []


def test_replace_favorite_genres_404_when_missing(client, db_session):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "fav2@example.com",
            "password": "Str0ngPassw0rd!",
            "username": "fav2",
        },
    )
    assert reg.status_code == 201, reg.text
    access = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    missing = uuid.uuid4()
    r = client.put(
        "/api/v1/profile/favorite-genres",
        headers=headers,
        json={"genre_ids": [str(missing)]},
    )
    assert r.status_code == 404
