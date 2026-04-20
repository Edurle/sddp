from datetime import timedelta

from app.models import User
from app.utils.security import create_access_token, hash_password
from tests.conftest import auth_headers


def _expired_headers(user_id, is_admin=True):
    token = create_access_token(
        {"sub": str(user_id), "is_admin": is_admin, "permissions": []},
        expires_delta=timedelta(seconds=-1),
    )
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 3.1 User list (GET /api/v1/admin/users) - TC-ADMIN-001~009
# ============================================================


async def test_admin_get_users_success(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    item = data["items"][0]
    for field in ("id", "email", "nickname", "is_active", "is_admin", "created_at"):
        assert field in item


async def test_admin_get_users_page2(client, admin_user, db):
    for i in range(25):
        db.add(User(
            email=f"bulk{i}@example.com",
            nickname=f"用户{i}",
            password_hash=hash_password("12345678"),
            is_active=True,
            is_admin=False,
            email_verified=True,
        ))
    await db.commit()

    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get("/api/v1/admin/users?page=2&page_size=20", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["page"] == 2
    assert len(body["data"]["items"]) <= 20


async def test_admin_get_users_custom_page_size(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get("/api/v1/admin/users?page=1&page_size=10", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["page_size"] == 10
    assert len(body["data"]["items"]) <= 10


async def test_admin_search_users_by_email(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get(
        f"/api/v1/admin/users?search={normal_user.email}", headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert any(item["email"] == normal_user.email for item in body["data"]["items"])


async def test_admin_search_users_by_nickname(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get(
        f"/api/v1/admin/users?search={normal_user.nickname}", headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert any(item["nickname"] == normal_user.nickname for item in body["data"]["items"])


async def test_admin_search_users_no_result(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.get("/api/v1/admin/users?search=不存在的用户", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


async def test_admin_get_users_non_admin(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40300


async def test_admin_get_users_not_logged_in(client, db):
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_admin_get_users_token_expired(client, admin_user, db):
    headers = _expired_headers(admin_user.id)
    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40101


# ============================================================
# 3.2 Create user (POST /api/v1/admin/users) - TC-ADMIN-010~021
# ============================================================


async def test_admin_create_user_success(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "newuser@example.com", "nickname": "新用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["email"] == "newuser@example.com"
    assert body["data"]["nickname"] == "新用户"
    assert body["data"]["is_active"] is True
    assert body["data"]["is_admin"] is False
    assert "id" in body["data"]
    assert "created_at" in body["data"]


async def test_admin_create_user_email_exists(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": normal_user.email, "nickname": "用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40002


async def test_admin_create_user_missing_email(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"nickname": "用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_missing_nickname(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "new@example.com", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_missing_password(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "new@example.com", "nickname": "用户"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_invalid_email(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "invalid", "nickname": "用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_password_too_short(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "new@example.com", "nickname": "用户", "password": "1234567"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_nickname_too_short(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "new@example.com", "nickname": "A", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_nickname_too_long(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"email": "new@example.com", "nickname": "A" * 33, "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_create_user_non_admin(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"email": "new@example.com", "nickname": "用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40300


async def test_admin_create_user_not_logged_in(client, db):
    data = {"email": "new@example.com", "nickname": "用户", "password": "12345678"}
    response = await client.post("/api/v1/admin/users", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_admin_create_user_empty_body(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.post("/api/v1/admin/users", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


# ============================================================
# 3.3 Toggle user status (PUT /api/v1/admin/users/{id}/status) - TC-ADMIN-022~030
# ============================================================


async def test_admin_disable_user(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"is_active": False}
    response = await client.put(
        f"/api/v1/admin/users/{normal_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["id"] == normal_user.id
    assert body["data"]["is_active"] is False


async def test_admin_enable_user(client, admin_user, disabled_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"is_active": True}
    response = await client.put(
        f"/api/v1/admin/users/{disabled_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["id"] == disabled_user.id
    assert body["data"]["is_active"] is True


async def test_admin_toggle_user_not_found(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"is_active": False}
    response = await client.put("/api/v1/admin/users/99999/status", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_admin_disable_self(client, admin_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"is_active": False}
    response = await client.put(
        f"/api/v1/admin/users/{admin_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_toggle_missing_is_active(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    response = await client.put(
        f"/api/v1/admin/users/{normal_user.id}/status", json={}, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_toggle_is_active_non_boolean(client, admin_user, normal_user, db):
    headers = auth_headers(admin_user.id, is_admin=True)
    data = {"is_active": "yes"}
    response = await client.put(
        f"/api/v1/admin/users/{normal_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_admin_toggle_user_non_admin(client, normal_user, admin_user, db):
    headers = auth_headers(normal_user.id)
    data = {"is_active": False}
    response = await client.put(
        f"/api/v1/admin/users/{admin_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40300


async def test_admin_toggle_user_not_logged_in(client, normal_user, db):
    data = {"is_active": False}
    response = await client.put(
        f"/api/v1/admin/users/{normal_user.id}/status", json=data,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_admin_toggle_user_token_expired(client, admin_user, normal_user, db):
    headers = _expired_headers(admin_user.id)
    data = {"is_active": False}
    response = await client.put(
        f"/api/v1/admin/users/{normal_user.id}/status", json=data, headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 40101
