import pytest
from tests.conftest import auth_headers


class TestReviewComments:
    @pytest.mark.asyncio
    async def test_approve_creates_review_comment(
        self, client, normal_user, another_user, sample_iteration, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        submit_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["code"] == 0

        reviewer_headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        review_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve", "comment": "看起来不错"},
            headers=reviewer_headers,
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["code"] == 0

        comments_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        assert comments_resp.status_code == 200
        body = comments_resp.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["action"] == "approve"
        assert body["data"][0]["comment"] == "看起来不错"
        assert body["data"][0]["reviewer_id"] == another_user.id

    @pytest.mark.asyncio
    async def test_reject_creates_review_comment(
        self, client, normal_user, another_user, sample_iteration, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        submit_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert submit_resp.json()["code"] == 0

        reviewer_headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        review_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": "需要修改"},
            headers=reviewer_headers,
        )
        assert review_resp.json()["code"] == 0

        comments_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        body = comments_resp.json()
        assert body["code"] == 0
        assert len(body["data"]) == 1
        assert body["data"][0]["action"] == "reject"
        assert body["data"][0]["comment"] == "需要修改"

    @pytest.mark.asyncio
    async def test_empty_comments_list(
        self, client, normal_user, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/review-comments",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == []
