import pytest

from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_webhook(client, owner_role, normal_user):
    team_id = owner_role["team"].id
    resp = await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook", "events": ["review.approved"]},
        headers=auth_headers(normal_user.id, permissions=["member:invite"]),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["url"] == "https://example.com/hook"
    assert data["events"] == ["review.approved"]
    assert data["is_active"] is True
    assert data["secret"] is None


@pytest.mark.asyncio
async def test_list_webhooks(client, owner_role, normal_user):
    team_id = owner_role["team"].id
    headers = auth_headers(normal_user.id, permissions=["member:invite"])
    await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook1"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook2"},
        headers=headers,
    )
    resp = await client.get(
        f"/api/v1/teams/{team_id}/webhooks",
        headers=auth_headers(normal_user.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) >= 2


@pytest.mark.asyncio
async def test_update_webhook(client, owner_role, normal_user):
    team_id = owner_role["team"].id
    headers = auth_headers(normal_user.id, permissions=["member:invite"])
    create_resp = await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook"},
        headers=headers,
    )
    wh_id = create_resp.json()["data"]["id"]
    resp = await client.put(
        f"/api/v1/teams/{team_id}/webhooks/{wh_id}",
        json={"url": "https://example.com/updated", "is_active": False},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["url"] == "https://example.com/updated"
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_delete_webhook(client, owner_role, normal_user):
    team_id = owner_role["team"].id
    headers = auth_headers(normal_user.id, permissions=["member:invite"])
    create_resp = await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook"},
        headers=headers,
    )
    wh_id = create_resp.json()["data"]["id"]
    resp = await client.delete(
        f"/api/v1/teams/{team_id}/webhooks/{wh_id}",
        headers=headers,
    )
    assert resp.status_code == 200
    list_resp = await client.get(
        f"/api/v1/teams/{team_id}/webhooks",
        headers=auth_headers(normal_user.id),
    )
    ids = [w["id"] for w in list_resp.json()["data"]]
    assert wh_id not in ids


@pytest.mark.asyncio
async def test_deliveries_list_empty(client, owner_role, normal_user):
    team_id = owner_role["team"].id
    headers = auth_headers(normal_user.id, permissions=["member:invite"])
    create_resp = await client.post(
        f"/api/v1/teams/{team_id}/webhooks",
        json={"url": "https://example.com/hook"},
        headers=headers,
    )
    wh_id = create_resp.json()["data"]["id"]
    resp = await client.get(
        f"/api/v1/teams/{team_id}/webhooks/{wh_id}/deliveries",
        headers=auth_headers(normal_user.id),
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []
