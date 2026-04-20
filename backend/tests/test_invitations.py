from app.models import Invitation, Team, TeamMember
from tests.conftest import auth_headers


async def test_get_pending_invitations_success(client, normal_user, another_user, db):
    team = Team(name="邀请团队", description="测试", owner_id=another_user.id)
    db.add(team)
    await db.flush()

    member = TeamMember(team_id=team.id, user_id=another_user.id)
    db.add(member)
    await db.flush()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=another_user.id,
        invitee_id=normal_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/invitations/pending", headers=headers)
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1


async def test_get_pending_invitations_empty(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.get("/api/v1/invitations/pending", headers=headers)
    body = response.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 0


async def test_accept_invitation(client, normal_user, another_user, db):
    team = Team(name="邀请团队", description="测试", owner_id=another_user.id)
    db.add(team)
    await db.flush()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=another_user.id,
        invitee_id=normal_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.put(
        f"/api/v1/invitations/{invitation.id}",
        json={"action": "accept"},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_reject_invitation(client, normal_user, another_user, db):
    team = Team(name="邀请团队", description="测试", owner_id=another_user.id)
    db.add(team)
    await db.flush()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=another_user.id,
        invitee_id=normal_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.put(
        f"/api/v1/invitations/{invitation.id}",
        json={"action": "reject"},
        headers=headers,
    )
    assert response.json()["code"] == 0


async def test_handle_invitation_not_found(client, normal_user, db):
    headers = auth_headers(normal_user.id)
    response = await client.put(
        "/api/v1/invitations/999",
        json={"action": "accept"},
        headers=headers,
    )
    assert response.json()["code"] == 40400


async def test_handle_invitation_already_processed(client, normal_user, another_user, db):
    team = Team(name="邀请团队", description="测试", owner_id=another_user.id)
    db.add(team)
    await db.flush()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=another_user.id,
        invitee_id=normal_user.id,
        status="accepted",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.put(
        f"/api/v1/invitations/{invitation.id}",
        json={"action": "accept"},
        headers=headers,
    )
    assert response.json()["code"] == 40005


async def test_handle_invitation_not_invitee(client, normal_user, another_user, db):
    team = Team(name="邀请团队", description="测试", owner_id=another_user.id)
    db.add(team)
    await db.flush()

    invitation = Invitation(
        team_id=team.id,
        inviter_id=another_user.id,
        invitee_id=another_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()

    headers = auth_headers(normal_user.id)
    response = await client.put(
        f"/api/v1/invitations/{invitation.id}",
        json={"action": "accept"},
        headers=headers,
    )
    assert response.json()["code"] == 40300
