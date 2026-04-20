from app.models import Role, RolePermission
from tests.conftest import auth_headers


async def test_get_roles_success(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}/roles", headers=headers)
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    role_data = body["data"][0]
    assert "permissions" in role_data


async def test_get_roles_includes_builtin(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}/roles", headers=headers)
    body = response.json()
    assert body["code"] == 0
    role_names = [r["name"] for r in body["data"]]
    assert "所有者" in role_names


async def test_create_role_success(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/roles",
        json={
            "name": "开发者",
            "description": "开发人员角色",
            "permissions": ["task:create", "task:edit"],
        },
        headers=headers,
    )
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["id"] is not None


async def test_create_role_duplicate_name(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    await client.post(
        f"/api/v1/teams/{team.id}/roles",
        json={
            "name": "开发者",
            "description": "开发人员角色",
            "permissions": ["task:create"],
        },
        headers=headers,
    )
    response = await client.post(
        f"/api/v1/teams/{team.id}/roles",
        json={
            "name": "开发者",
            "description": "重复角色",
            "permissions": ["task:edit"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40007


async def test_create_role_empty_name(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/roles",
        json={
            "name": "",
            "description": "空名称",
            "permissions": ["task:create"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40001


async def test_create_role_no_permission(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/roles",
        json={
            "name": "开发者",
            "description": "开发人员角色",
            "permissions": ["task:create", "task:edit"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40300


async def test_update_role_success(client, normal_user, owner_role, db):
    team = owner_role["team"]

    role = Role(team_id=team.id, name="自定义角色", is_builtin=False)
    db.add(role)
    await db.flush()

    db.add(RolePermission(role_id=role.id, permission="task:create"))
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/roles/{role.id}",
        json={
            "name": "高级开发者",
            "permissions": ["task:create", "task:edit"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_update_role_builtin_forbidden(client, normal_user, owner_role, db):
    team = owner_role["team"]
    builtin_role = owner_role["role"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/roles/{builtin_role.id}",
        json={
            "name": "修改所有者",
            "permissions": ["task:create"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40009


async def test_update_role_not_found(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/roles/999",
        json={
            "name": "不存在",
            "permissions": ["task:create"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_update_role_soft_deleted_forbidden(client, normal_user, owner_role, db):
    team = owner_role["team"]

    role = Role(team_id=team.id, name="已删除角色", is_builtin=False, is_deleted=True)
    db.add(role)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/roles/{role.id}",
        json={
            "name": "修改已删除",
            "permissions": ["task:create"],
        },
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_delete_role_success(client, normal_user, owner_role, db):
    team = owner_role["team"]

    role = Role(team_id=team.id, name="待删除角色", is_builtin=False)
    db.add(role)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.delete(
        f"/api/v1/teams/{team.id}/roles/{role.id}",
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_delete_role_builtin_forbidden(client, normal_user, owner_role, db):
    team = owner_role["team"]
    builtin_role = owner_role["role"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.delete(
        f"/api/v1/teams/{team.id}/roles/{builtin_role.id}",
        headers=headers,
    )
    assert response.json()["code"] == 40009


async def test_delete_role_not_in_list(client, normal_user, owner_role, db):
    team = owner_role["team"]

    role = Role(team_id=team.id, name="待删除角色", is_builtin=False)
    db.add(role)
    await db.commit()
    role_id = role.id

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    await client.delete(
        f"/api/v1/teams/{team.id}/roles/{role_id}",
        headers=headers,
    )

    list_response = await client.get(
        f"/api/v1/teams/{team.id}/roles",
        headers=auth_headers(normal_user.id),
    )
    body = list_response.json()
    assert body["code"] == 0
    role_ids = [r["id"] for r in body["data"]]
    assert role_id not in role_ids
