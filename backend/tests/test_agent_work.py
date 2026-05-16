import pytest
from tests.conftest import auth_headers


class TestAgentWork:
    @pytest.mark.asyncio
    async def test_empty_work(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/users/me/work", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert "pending_reviews" in data
        assert "assigned_tasks" in data
        assert "draftable_items" in data
        assert "summary" in data
        assert data["summary"]["reviews_waiting"] == 0
        assert data["summary"]["tasks_in_progress"] == 0
        assert data["summary"]["items_to_draft"] == 0

    @pytest.mark.asyncio
    async def test_shows_pending_review(
        self, client, normal_user, another_user, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )

        reviewer_headers = auth_headers(another_user.id)
        resp = await client.get("/api/v1/users/me/work", headers=reviewer_headers)
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["summary"]["reviews_waiting"] >= 1

    @pytest.mark.asyncio
    async def test_shows_assigned_task(
        self, client, normal_user, approved_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["task:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/tasks",
            json={"title": "Test task", "assignee_id": normal_user.id},
            headers=headers,
        )

        resp = await client.get("/api/v1/users/me/work", headers=auth_headers(normal_user.id))
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["summary"]["tasks_in_progress"] >= 1
