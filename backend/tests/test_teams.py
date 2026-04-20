import pytest
from tests.conftest import auth_headers


async def test_create_team_success(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.post(
        "/api/v1/teams/",
        json={"name": "团队A", "description": "描述"},
        headers=headers,
    )
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["id"] is not None
    assert body["data"]["name"] == "团队A"


async def test_create_team_creator_is_owner(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.post(
        "/api/v1/teams/",
        json={"name": "团队B", "description": "描述"},
        headers=headers,
    )
    body = response.json()
    assert body["code"] == 0
    team_id = body["data"]["id"]

    detail = await client.get(f"/api/v1/teams/{team_id}", headers=headers)
    detail_body = detail.json()
    assert detail_body["code"] == 0
    assert detail_body["data"]["owner"]["id"] == normal_user.id


async def test_create_team_empty_name(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.post(
        "/api/v1/teams/",
        json={"name": "", "description": ""},
        headers=headers,
    )
    assert response.json()["code"] == 40001


async def test_create_team_not_logged_in(client, db):
    response = await client.post(
        "/api/v1/teams/",
        json={"name": "团队A"},
    )
    assert response.json()["code"] == 40100


async def test_get_team_success(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}", headers=headers)
    body = response.json()
    assert body["code"] == 0
    assert "owner" in body["data"]
    assert "member_count" in body["data"]


async def test_get_team_not_found(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/teams/999", headers=headers)
    assert response.json()["code"] == 40400


async def test_get_team_non_member_forbidden(client, normal_user, another_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(another_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}", headers=headers)
    assert response.json()["code"] == 40300


async def test_update_team_owner_success(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": "新名称", "description": "新描述"},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_update_team_admin_success(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id, permissions=["member:assign_role"])
    response = await client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": "新名称", "description": "新描述"},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_update_team_regular_member_forbidden(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id)
    response = await client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": "新名称", "description": "新描述"},
        headers=headers,
    )
    assert response.json()["code"] == 40300


async def test_update_team_empty_name(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}",
        json={"name": ""},
        headers=headers,
    )
    assert response.json()["code"] == 40001


async def test_dissolve_team_success(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.delete(
        f"/api/v1/teams/{team.id}",
        headers={**headers, "X-Confirm-Delete": team.name},
    )
    assert response.json()["code"] == 0


async def test_dissolve_team_wrong_confirm(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.delete(
        f"/api/v1/teams/{team.id}",
        headers={**headers, "X-Confirm-Delete": "错误名"},
    )
    assert response.json()["code"] == 40001


async def test_dissolve_team_non_owner_rejected(client, another_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(another_user.id)
    response = await client.delete(
        f"/api/v1/teams/{team.id}",
        headers={**headers, "X-Confirm-Delete": team.name},
    )
    assert response.json()["code"] == 40300


async def test_dissolve_team_then_query_404(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    await client.delete(
        f"/api/v1/teams/{team.id}",
        headers={**headers, "X-Confirm-Delete": team.name},
    )
    response = await client.get(f"/api/v1/teams/{team.id}", headers=headers)
    assert response.json()["code"] == 40400


async def test_transfer_team_success(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/transfer",
        json={"new_owner_id": another_user.id},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_transfer_team_new_owner_not_in_team(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/transfer",
        json={"new_owner_id": 999},
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_transfer_team_non_owner_rejected(client, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/transfer",
        json={"new_owner_id": another_user.id},
        headers=headers,
    )
    assert response.json()["code"] == 40300


async def test_transfer_team_to_self(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/transfer",
        json={"new_owner_id": normal_user.id},
        headers=headers,
    )
    assert response.json()["code"] == 40001
