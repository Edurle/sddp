async def test_login_success(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "token" in body["data"]
    assert "user" in body["data"]
    assert body["data"]["user"]["email"] == "user@example.com"


async def test_login_wrong_password(client, normal_user, db):
    data = {"email": "user@example.com", "password": "wrongpass1"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40003


async def test_login_user_not_found(client, db):
    data = {"email": "nobody@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40003


async def test_login_email_unverified(client, unverified_user, db):
    data = {"email": "unverified@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40004


async def test_login_remember_true(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678", "remember": True}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 0


async def test_login_remember_false(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678", "remember": False}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 0


async def test_login_missing_email(client, db):
    data = {"password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_missing_password(client, db):
    data = {"email": "user@example.com"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_invalid_email_format(client, db):
    data = {"email": "not-an-email", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_empty_body(client, db):
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 200
    assert response.json()["code"] == 40001
