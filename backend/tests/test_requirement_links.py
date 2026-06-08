import pytest
from tests.conftest import auth_headers


class TestSupersedeRequirement:
    @pytest.mark.asyncio
    async def test_supersede_approved_requirement_success(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["old_requirement"]["status"] == "deprecated"
        assert data["new_requirement"]["status"] == "drafting_req"
        assert data["new_requirement"]["title"].endswith("（变更）")
        assert data["new_requirement"]["iteration_id"] == approved_requirement.iteration_id

    @pytest.mark.asyncio
    async def test_supersede_with_custom_title(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            json={"title": "自定义变更标题"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["new_requirement"]["title"] == "自定义变更标题"

    @pytest.mark.asyncio
    async def test_supersede_non_approved_forbidden(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/supersede",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_supersede_not_found(
        self, client, normal_user
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            "/api/v1/requirements/999/supersede",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400

    @pytest.mark.asyncio
    async def test_supersede_creates_link(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )
        assert resp.status_code == 200

        headers2 = auth_headers(normal_user.id)
        resp2 = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/links",
            headers=headers2,
        )
        assert resp2.status_code == 200
        links = resp2.json()["data"]
        assert len(links) == 1
        assert links[0]["link_type"] == "supersede"
        assert links[0]["source_id"] == approved_requirement.id

    @pytest.mark.asyncio
    async def test_supersede_chain(
        self, client, normal_user, approved_requirement, db
    ):
        from app.models import Requirement
        from sqlalchemy import select

        headers = auth_headers(normal_user.id, permissions=["requirement:create"])

        resp1 = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )
        new_req_id = resp1.json()["data"]["new_requirement"]["id"]

        stmt = select(Requirement).where(Requirement.id == new_req_id)
        new_req = (await db.execute(stmt)).scalar_one()
        new_req.status = "approved"
        await db.commit()

        resp2 = await client.post(
            f"/api/v1/requirements/{new_req_id}/supersede",
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["old_requirement"]["status"] == "deprecated"

        headers2 = auth_headers(normal_user.id)
        resp3 = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/links",
            headers=headers2,
        )
        links = resp3.json()["data"]
        assert len(links) == 1

        new_req_id2 = resp2.json()["data"]["new_requirement"]["id"]
        resp4 = await client.get(
            f"/api/v1/requirements/{new_req_id2}/links",
            headers=headers2,
        )
        links2 = resp4.json()["data"]
        assert len(links2) == 1
        assert links2[0]["link_type"] == "supersede"

    @pytest.mark.asyncio
    async def test_supersede_no_permission(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestRequirementLinks:
    @pytest.mark.asyncio
    async def test_create_relates_to_link_success(
        self, client, normal_user, sample_requirement, db
    ):
        from app.models import Requirement

        req2 = Requirement(
            iteration_id=sample_requirement.iteration_id,
            title="另一个需求",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req2)
        await db.commit()
        await db.refresh(req2)

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": req2.id, "link_type": "relates_to"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["link_type"] == "relates_to"

    @pytest.mark.asyncio
    async def test_create_link_to_self_forbidden(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": sample_requirement.id, "link_type": "relates_to"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_duplicate_link_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        from app.models import Requirement

        req2 = Requirement(
            iteration_id=sample_requirement.iteration_id,
            title="另一个需求",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req2)
        await db.commit()
        await db.refresh(req2)

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": req2.id, "link_type": "relates_to"},
            headers=headers,
        )
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": req2.id, "link_type": "relates_to"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_supersede_link_manually_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        from app.models import Requirement

        req2 = Requirement(
            iteration_id=sample_requirement.iteration_id,
            title="另一个需求",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req2)
        await db.commit()
        await db.refresh(req2)

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": req2.id, "link_type": "supersede"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_list_links_empty(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"] == []

    @pytest.mark.asyncio
    async def test_delete_relates_to_link_success(
        self, client, normal_user, sample_requirement, db
    ):
        from app.models import Requirement

        req2 = Requirement(
            iteration_id=sample_requirement.iteration_id,
            title="另一个需求",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req2)
        await db.commit()
        await db.refresh(req2)

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        create_resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/links",
            json={"target_id": req2.id, "link_type": "relates_to"},
            headers=headers,
        )
        link_id = create_resp.json()["data"]["id"]

        delete_resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}/links/{link_id}",
            headers=headers,
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_delete_supersede_link_forbidden(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        supersede_resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )
        assert supersede_resp.status_code == 200

        headers2 = auth_headers(normal_user.id)
        links_resp = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/links",
            headers=headers2,
        )
        link_id = links_resp.json()["data"][0]["id"]

        delete_resp = await client.delete(
            f"/api/v1/requirements/{approved_requirement.id}/links/{link_id}",
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        body = delete_resp.json()
        assert body["code"] == 40001


class TestDeprecatedLockdown:
    @pytest.mark.asyncio
    async def test_deprecated_requirement_cannot_edit(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        edit_headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{approved_requirement.id}",
            json={"title": "尝试修改"},
            headers=edit_headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_cannot_delete(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        delete_headers = auth_headers(normal_user.id, permissions=["requirement:delete"])
        resp = await client.delete(
            f"/api/v1/requirements/{approved_requirement.id}",
            headers=delete_headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_cannot_submit_review(
        self, client, normal_user, another_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        review_headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=review_headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_task_cannot_edit(
        self, client, normal_user, approved_requirement, sample_task, db
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        from app.api import tasks as tasks_api
        edit_resp = await client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json={"title": "尝试修改"},
            headers=auth_headers(normal_user.id, permissions=["task:edit"]),
        )
        body = edit_resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_task_cannot_delete(
        self, client, normal_user, approved_requirement, sample_task
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        delete_resp = await client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers=auth_headers(normal_user.id, permissions=["task:delete"]),
        )
        body = delete_resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_test_case_cannot_edit(
        self, client, normal_user, approved_requirement, sample_test_case
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        edit_resp = await client.put(
            f"/api/v1/test-cases/{sample_test_case.id}",
            json={"title": "尝试修改"},
            headers=auth_headers(normal_user.id, permissions=["test_case:edit"]),
        )
        body = edit_resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_deprecated_requirement_test_case_cannot_delete(
        self, client, normal_user, approved_requirement, sample_test_case
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        delete_resp = await client.delete(
            f"/api/v1/test-cases/{sample_test_case.id}",
            headers=auth_headers(normal_user.id, permissions=["test_case:delete"]),
        )
        body = delete_resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_requirement_detail_includes_links(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            headers=headers,
        )

        detail_resp = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}",
            headers=auth_headers(normal_user.id),
        )
        body = detail_resp.json()
        assert body["code"] == 0
        assert "links" in body["data"]
        assert len(body["data"]["links"]) == 1
        assert body["data"]["links"][0]["link_type"] == "supersede"
