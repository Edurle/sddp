import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.models.api_key import ApiKey


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def _create_api_key_in_db(db, user_id: int, name: str = "test-key", **kwargs) -> tuple[ApiKey, str]:
    raw_key = f"sdd_{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    key_prefix = raw_key[:8]
    api_key = ApiKey(
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        user_id=user_id,
        **kwargs,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key, raw_key


@pytest.mark.asyncio
async def test_tc_agent_001_admin_creates_api_key(client, admin_user):
    resp = await client.post(
        "/api/v1/admin/api-keys",
        json={"user_id": admin_user.id, "name": "agent-key"},
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "raw_key" in data
    assert data["raw_key"].startswith("sdd_")
    assert data["name"] == "agent-key"
    assert data["key_prefix"] == data["raw_key"][:8]
    assert data["user_id"] == admin_user.id


@pytest.mark.asyncio
async def test_tc_agent_002_create_without_expiry(client, admin_user):
    resp = await client.post(
        "/api/v1/admin/api-keys",
        json={"user_id": admin_user.id, "name": "no-expiry"},
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_tc_agent_003_non_admin_cannot_create(client, normal_user):
    resp = await client.post(
        "/api/v1/admin/api-keys",
        json={"user_id": normal_user.id, "name": "blocked"},
        headers=auth_headers(normal_user.id, is_admin=False),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40300


@pytest.mark.asyncio
async def test_tc_agent_004_user_not_found(client):
    resp = await client.post(
        "/api/v1/admin/api-keys",
        json={"user_id": 99999, "name": "ghost"},
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


@pytest.mark.asyncio
async def test_tc_agent_005_empty_name(client, admin_user):
    resp = await client.post(
        "/api/v1/admin/api-keys",
        json={"user_id": admin_user.id, "name": ""},
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40001


@pytest.mark.asyncio
async def test_tc_agent_006_valid_key_accesses_protected_endpoint(client, normal_user, db):
    _, raw_key = await _create_api_key_in_db(db, normal_user.id)

    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_tc_agent_007_invalid_key(client):
    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": "sdd_invalid_key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40100


@pytest.mark.asyncio
async def test_tc_agent_008_revoked_key(client, normal_user, db):
    api_key, raw_key = await _create_api_key_in_db(db, normal_user.id)
    api_key.is_active = False
    await db.commit()

    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40100


@pytest.mark.asyncio
async def test_tc_agent_009_expired_key(client, normal_user, db):
    api_key, raw_key = await _create_api_key_in_db(
        db, normal_user.id, expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40100


@pytest.mark.asyncio
async def test_tc_agent_010_key_with_disabled_user(client, db):
    from app.models import User
    from app.utils.security import hash_password

    user = User(
        email="disabled-for-key@example.com",
        nickname="Disabled",
        password_hash=hash_password("12345678"),
        is_active=False,
        is_admin=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    _, raw_key = await _create_api_key_in_db(db, user.id)

    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40100


@pytest.mark.asyncio
async def test_tc_agent_011_key_permissions_are_fresh(client, db, normal_user, owner_role):
    _, raw_key = await _create_api_key_in_db(db, normal_user.id)

    resp = await client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["id"] == normal_user.id


@pytest.mark.asyncio
async def test_tc_agent_012_both_jwt_and_api_key_api_key_priority(client, admin_user, db):
    _, raw_key = await _create_api_key_in_db(db, admin_user.id)

    resp = await client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": f"Bearer {_make_admin_token()}",
            "X-API-Key": raw_key,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_tc_agent_013_list_user_keys(client, admin_user, db):
    await _create_api_key_in_db(db, admin_user.id, name="key-1")
    await _create_api_key_in_db(db, admin_user.id, name="key-2")

    resp = await client.get(
        f"/api/v1/admin/users/{admin_user.id}/api-keys",
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    keys = body["data"]
    assert len(keys) == 2
    for k in keys:
        assert "key_prefix" in k
        assert "raw_key" not in k


@pytest.mark.asyncio
async def test_tc_agent_014_non_admin_cannot_list(client, normal_user):
    resp = await client.get(
        f"/api/v1/admin/users/{normal_user.id}/api-keys",
        headers=auth_headers(normal_user.id, is_admin=False),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40300


@pytest.mark.asyncio
async def test_tc_agent_015_revoke_key(client, admin_user, db):
    api_key, _ = await _create_api_key_in_db(db, admin_user.id, name="to-revoke")

    resp = await client.delete(
        f"/api/v1/admin/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0

    await db.refresh(api_key)
    assert api_key.is_active is False


@pytest.mark.asyncio
async def test_tc_agent_016_revoke_twice_idempotent(client, admin_user, db):
    api_key, _ = await _create_api_key_in_db(db, admin_user.id)

    resp1 = await client.delete(
        f"/api/v1/admin/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp1.json()["code"] == 0

    resp2 = await client.delete(
        f"/api/v1/admin/api-keys/{api_key.id}",
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp2.json()["code"] == 0


@pytest.mark.asyncio
async def test_tc_agent_017_revoke_nonexistent(client):
    resp = await client.delete(
        "/api/v1/admin/api-keys/99999",
        headers={"Authorization": f"Bearer {_make_admin_token()}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


def _make_admin_token() -> str:
    from app.utils.security import create_access_token

    return create_access_token({"sub": "1", "is_admin": True, "permissions": []})


def auth_headers(user_id: int, is_admin: bool = False, permissions: list | None = None) -> dict:
    from app.utils.security import create_access_token

    token = create_access_token({
        "sub": str(user_id),
        "is_admin": is_admin,
        "permissions": permissions or [],
    })
    return {"Authorization": f"Bearer {token}"}
