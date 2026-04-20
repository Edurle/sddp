from datetime import timedelta

from app.utils.security import create_access_token
from tests.conftest import auth_headers


def _expired_headers(user_id, is_admin=False):
    token = create_access_token(
        {"sub": str(user_id), "is_admin": is_admin, "permissions": []},
        expires_delta=timedelta(seconds=-1),
    )
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# 2.1 Get current user (GET /api/v1/users/me) - TC-USER-001~004
# ============================================================


async def test_get_current_user_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["id"] == normal_user.id
    assert data["email"] == normal_user.email
    assert "nickname" in data
    assert "avatar" in data
    assert "is_admin" in data
    assert "teams" in data


async def test_get_current_user_not_logged_in(client, db):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_get_current_user_token_expired(client, normal_user, db):
    headers = _expired_headers(normal_user.id)
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40101


async def test_get_current_user_invalid_token(client, db):
    headers = {"Authorization": "Bearer invalid-token-here"}
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40100


# ============================================================
# 2.2 Update user info (PUT /api/v1/users/me) - TC-USER-005~013
# ============================================================


async def test_update_nickname_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"nickname": "新昵称"}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "新昵称"


async def test_update_avatar_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"avatar": "https://example.com/new.jpg"}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["avatar"] == "https://example.com/new.jpg"


async def test_update_nickname_and_avatar(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"nickname": "昵称", "avatar": "https://example.com/new.jpg"}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["nickname"] == "昵称"
    assert body["data"]["avatar"] == "https://example.com/new.jpg"


async def test_update_empty_nickname(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"nickname": ""}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_update_nickname_too_short(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"nickname": "A"}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_update_nickname_too_long(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"nickname": "A" * 33}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_update_no_fields(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.put("/api/v1/users/me", json={}, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_update_not_logged_in(client, db):
    data = {"nickname": "昵称"}
    response = await client.put("/api/v1/users/me", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_update_token_expired(client, normal_user, db):
    headers = _expired_headers(normal_user.id)
    data = {"nickname": "昵称"}
    response = await client.put("/api/v1/users/me", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40101


# ============================================================
# 2.3 Change password (PUT /api/v1/users/me/password) - TC-USER-014~021
# ============================================================


async def test_change_password_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"old_password": "12345678", "new_password": "newpass12"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "密码修改成功" in body["message"]


async def test_change_password_wrong_old(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"old_password": "wrongpass1", "new_password": "newpass12"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40003


async def test_change_password_new_too_short(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"old_password": "12345678", "new_password": "1234567"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_change_password_new_too_long(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"old_password": "12345678", "new_password": "a" * 65}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_change_password_missing_old(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"new_password": "newpass12"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_change_password_missing_new(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    data = {"old_password": "12345678"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_change_password_not_logged_in(client, db):
    data = {"old_password": "12345678", "new_password": "newpass12"}
    response = await client.put("/api/v1/users/me/password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_change_password_token_expired(client, normal_user, db):
    headers = _expired_headers(normal_user.id)
    data = {"old_password": "12345678", "new_password": "newpass12"}
    response = await client.put("/api/v1/users/me/password", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40101


# ============================================================
# 2.4 Get pending items (GET /api/v1/users/me/pending) - TC-USER-022~025
# ============================================================


async def test_get_pending_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/users/me/pending", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert "pending_reviews" in data
    assert "pending_tasks" in data
    assert "pending_invitations" in data


async def test_get_pending_empty(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/users/me/pending", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["pending_reviews"] == []
    assert data["pending_tasks"] == []
    assert data["pending_invitations"] == []


async def test_get_pending_not_logged_in(client, db):
    response = await client.get("/api/v1/users/me/pending")
    assert response.status_code == 200
    assert response.json()["code"] == 40100


async def test_get_pending_token_expired(client, normal_user, db):
    headers = _expired_headers(normal_user.id)
    response = await client.get("/api/v1/users/me/pending", headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 40101
