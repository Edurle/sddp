from app.models import Invitation, Role, RolePermission, MemberRole, TeamMember
from tests.conftest import auth_headers


async def test_get_members_success(client, normal_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}/members", headers=headers)
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1


async def test_get_members_filter_by_role(client, normal_user, team_with_members, db):
    team = team_with_members["team"]
    role = team_with_members["owner_role"]
    headers = auth_headers(normal_user.id)
    response = await client.get(
        f"/api/v1/teams/{team.id}/members?role_id={role.id}",
        headers=headers,
    )
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)


async def test_get_members_excludes_removed(client, normal_user, another_user, owner_role, db):
    team = owner_role["team"]
    member = TeamMember(
        team_id=team.id, user_id=another_user.id, is_deleted=True
    )
    db.add(member)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.get(f"/api/v1/teams/{team.id}/members", headers=headers)
    body = response.json()
    assert body["code"] == 0
    member_ids = [m["user_id"] for m in body["data"]]
    assert another_user.id not in member_ids


async def test_invite_member_success(client, normal_user, another_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"identifier": another_user.email},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_invite_member_user_not_found(client, normal_user, owner_role, db):
    team = owner_role["team"]
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"identifier": "nonexistent@example.com"},
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_invite_member_already_in_team(client, normal_user, team_with_members, db):
    team = team_with_members["team"]
    another = team_with_members["other_member"].user_id
    headers = auth_headers(normal_user.id, permissions=["member:invite"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"identifier": "other@example.com"},
        headers=headers,
    )
    assert response.json()["code"] == 40006


async def test_invite_member_pending_invitation_exists(client, normal_user, another_user, owner_role, db):
    team = owner_role["team"]
    invitation = Invitation(
        team_id=team.id,
        inviter_id=normal_user.id,
        invitee_id=another_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"identifier": another_user.email},
        headers=headers,
    )
    assert response.json()["code"] == 40001


async def test_invite_member_no_permission(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id)
    response = await client.post(
        f"/api/v1/teams/{team.id}/invitations",
        json={"identifier": "user@example.com"},
        headers=headers,
    )
    assert response.json()["code"] == 40300


async def test_remove_member_success(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id, permissions=["member:remove"])
    response = await client.delete(
        f"/api/v1/teams/{team.id}/members/{another_user.id}",
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_remove_member_cannot_remove_owner(client, normal_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id, permissions=["member:remove"])
    response = await client.delete(
        f"/api/v1/teams/{team.id}/members/{normal_user.id}",
        headers=headers,
    )
    assert response.json()["code"] == 40008


async def test_remove_member_no_permission(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(another_user.id)
    response = await client.delete(
        f"/api/v1/teams/{team.id}/members/{normal_user.id}",
        headers=headers,
    )
    assert response.json()["code"] == 40300


async def test_remove_member_not_in_list(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id, permissions=["member:remove"])
    await client.delete(
        f"/api/v1/teams/{team.id}/members/{another_user.id}",
        headers=headers,
    )

    list_response = await client.get(
        f"/api/v1/teams/{team.id}/members",
        headers=auth_headers(normal_user.id),
    )
    body = list_response.json()
    assert body["code"] == 0
    member_ids = [m["user_id"] for m in body["data"]]
    assert another_user.id not in member_ids


async def test_assign_roles_success(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    role = team_with_members["owner_role"]
    headers = auth_headers(normal_user.id, permissions=["member:assign_role"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/members/{another_user.id}/roles",
        json={"role_ids": [role.id]},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_assign_roles_not_found(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]
    headers = auth_headers(normal_user.id, permissions=["member:assign_role"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/members/{another_user.id}/roles",
        json={"role_ids": [999]},
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_assign_roles_multi_permission_union(client, normal_user, another_user, team_with_members, db):
    team = team_with_members["team"]

    role_a = Role(team_id=team.id, name="角色A", is_builtin=False)
    role_b = Role(team_id=team.id, name="角色B", is_builtin=False)
    db.add_all([role_a, role_b])
    await db.flush()

    db.add(RolePermission(role_id=role_a.id, permission="task:create"))
    db.add(RolePermission(role_id=role_b.id, permission="task:edit"))
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=["member:assign_role"])
    response = await client.put(
        f"/api/v1/teams/{team.id}/members/{another_user.id}/roles",
        json={"role_ids": [role_a.id, role_b.id]},
        headers=headers,
    )
    assert response.json()["code"] == 0
