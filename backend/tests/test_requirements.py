import pytest
from tests.conftest import auth_headers


class TestListRequirements:
    @pytest.mark.asyncio
    async def test_list_requirements_success(
        self, client, normal_user, sample_iteration, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], dict)
        assert "items" in body["data"]
        assert len(body["data"]["items"]) >= 1
        item = body["data"]["items"][0]
        assert item["id"] == sample_requirement.id
        assert "title" in item
        assert "req_type" in item
        assert "priority" in item
        assert "status" in item
        assert "task_count" in item
        assert "created_by" in item
        assert "created_at" in item

    @pytest.mark.asyncio
    async def test_list_requirements_filter_by_status(
        self, client, normal_user, sample_iteration, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements?status=drafting_req",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert all(r["status"] == "drafting_req" for r in body["data"]["items"])

    @pytest.mark.asyncio
    async def test_list_requirements_filter_by_req_type(
        self, client, normal_user, sample_iteration, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements?req_type=bug",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert all(r["req_type"] == "bug" for r in body["data"]["items"])

    @pytest.mark.asyncio
    async def test_list_requirements_sort_by_priority_desc(
        self, client, normal_user, sample_iteration, sample_requirement, db
    ):
        from app.models import Requirement

        req2 = Requirement(
            iteration_id=sample_iteration.id,
            title="高优先级",
            req_type="bug",
            priority=99,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req2)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements?sort_by=priority&sort_order=desc",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        priorities = [r["priority"] for r in body["data"]["items"]]
        assert priorities == sorted(priorities, reverse=True)

    @pytest.mark.asyncio
    async def test_list_requirements_sort_by_created_at_asc(
        self, client, normal_user, sample_iteration, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements?sort_by=created_at&sort_order=asc",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1

    @pytest.mark.asyncio
    async def test_list_requirements_empty_for_new_iteration(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]["items"]) >= 1


    @pytest.mark.asyncio
    async def test_list_requirements_empty_for_new_iteration(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], dict)
        assert body["data"]["items"] == []

    @pytest.mark.asyncio
    async def test_list_requirements_excludes_soft_deleted(
        self, client, normal_user, sample_iteration, sample_requirement, db
    ):
        from datetime import datetime, timezone

        sample_requirement.is_deleted = True
        sample_requirement.deleted_at = datetime.now(timezone.utc)
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        ids = [r["id"] for r in body["data"]["items"]]
        assert sample_requirement.id not in ids

    @pytest.mark.asyncio
    async def test_list_requirements_non_member_forbidden(
        self, client, another_user, sample_iteration
    ):
        headers = auth_headers(another_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestCreateRequirement:
    @pytest.mark.asyncio
    async def test_create_feature_requirement_success(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "用户管理",
                "req_type": "feature",
                "priority": 10,
                "description": "实现用户CRUD",
                "type_detail": {"feature_description": "包含注册登录等功能"},
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "id" in body["data"]

    @pytest.mark.asyncio
    async def test_create_optimization_requirement_success(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "性能优化",
                "req_type": "optimization",
                "priority": 5,
                "description": "优化查询性能",
                "type_detail": {"change_description": "重写数据库查询逻辑"},
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_create_bug_requirement_success(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "登录页面崩溃",
                "req_type": "bug",
                "priority": 20,
                "description": "登录页面在某些情况下崩溃",
                "type_detail": {
                    "bug_steps": "1. 打开登录页 2. 输入特殊字符 3. 点击登录",
                    "expected_behavior": "应提示输入错误",
                    "actual_behavior": "页面崩溃",
                    "fix_description": "需要增加输入校验",
                },
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_create_requirement_without_type_detail(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "无详情需求",
                "req_type": "feature",
                "priority": 1,
                "description": "测试无type_detail",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_create_requirement_missing_title(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "",
                "req_type": "feature",
                "priority": 1,
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_requirement_invalid_req_type(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "测试需求",
                "req_type": "invalid",
                "priority": 1,
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_requirement_no_permission(
        self, client, normal_user, another_user, sample_iteration
    ):
        headers = auth_headers(another_user.id)
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "用户管理",
                "req_type": "feature",
                "priority": 1,
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_create_requirement_not_logged_in(
        self, client, sample_iteration
    ):
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "用户管理",
                "req_type": "feature",
                "priority": 1,
            },
        )
        body = resp.json()
        assert body["code"] == 40100


class TestGetRequirementDetail:
    @pytest.mark.asyncio
    async def test_get_requirement_detail_success(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["id"] == sample_requirement.id
        assert "title" in data
        assert "req_type" in data
        assert "status" in data
        assert "description" in data
        assert "type_detail" in data
        assert "iteration" in data
        assert "current_step" in data
        assert "reviews" in data
        assert "tasks" in data
        assert "created_by" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_requirement_not_found(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            "/api/v1/requirements/999",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400

    @pytest.mark.asyncio
    async def test_get_requirement_soft_deleted(
        self, client, normal_user, sample_requirement, db
    ):
        from datetime import datetime, timezone

        sample_requirement.is_deleted = True
        sample_requirement.deleted_at = datetime.now(timezone.utc)
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400


class TestUpdateRequirement:
    @pytest.mark.asyncio
    async def test_update_requirement_in_drafting_req_success(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={
                "title": "更新后的标题",
                "type_detail": {"feature_description": "更新后的描述"},
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_update_requirement_in_reviewing_req_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "尝试修改"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_update_requirement_in_drafting_spec_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "尝试修改"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_update_requirement_in_approved_forbidden(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{approved_requirement.id}",
            json={"title": "尝试修改已通过需求"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_update_requirement_no_permission(
        self, client, normal_user, another_user, sample_requirement
    ):
        headers = auth_headers(another_user.id)
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "尝试修改"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_update_requirement_after_rejection_back_to_drafting(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={
                "title": "驳回后可重新编辑",
                "type_detail": {"feature_description": "修改后的描述"},
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0


class TestDeleteRequirement:
    @pytest.mark.asyncio
    async def test_delete_requirement_in_drafting_req_success(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:delete"])
        resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_delete_requirement_in_reviewing_req_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:delete"])
        resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_delete_requirement_in_approved_forbidden(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:delete"])
        resp = await client.delete(
            f"/api/v1/requirements/{approved_requirement.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_delete_requirement_no_permission(
        self, client, normal_user, another_user, sample_requirement
    ):
        headers = auth_headers(another_user.id)
        resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestSubmitReview:
    @pytest.mark.asyncio
    async def test_submit_review_from_drafting_req_to_reviewing_req(
        self, client, normal_user, another_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_submit_review_from_drafting_spec_to_reviewing_spec(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_submit_review_from_drafting_tests_to_reviewing_tests(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_tests"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_submit_review_in_reviewing_req_forbidden(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_submit_review_in_approved_forbidden(
        self, client, normal_user, another_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_submit_review_reviewer_not_found(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": 999},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400

    @pytest.mark.asyncio
    async def test_submit_review_not_creator_forbidden(
        self, client, another_user, sample_requirement
    ):
        headers = auth_headers(another_user.id, permissions=["requirement:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_submit_review_creator_without_permission(
        self, client, normal_user, another_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_submit_review_non_creator_with_db_permission(
        self, client, another_user, sample_requirement, owner_role, db
    ):
        from app.models import TeamMember, MemberRole, Role, RolePermission

        team = owner_role["team"]
        member = TeamMember(team_id=team.id, user_id=another_user.id)
        db.add(member)
        await db.flush()
        role = Role(team_id=team.id, name="提交审核", is_builtin=False)
        db.add(role)
        await db.flush()
        db.add(RolePermission(role_id=role.id, permission="requirement:submit_review_req"))
        await db.flush()
        db.add(MemberRole(member_id=member.id, role_id=role.id))
        await db.commit()

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_submit_review_non_creator_wrong_permission(
        self, client, another_user, sample_requirement, owner_role, db
    ):
        from app.models import TeamMember, MemberRole, Role, RolePermission

        team = owner_role["team"]
        member = TeamMember(team_id=team.id, user_id=another_user.id)
        db.add(member)
        await db.flush()
        role = Role(team_id=team.id, name="编辑需求", is_builtin=False)
        db.add(role)
        await db.flush()
        db.add(RolePermission(role_id=role.id, permission="requirement:edit"))
        await db.flush()
        db.add(MemberRole(member_id=member.id, role_id=role.id))
        await db.commit()

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestReview:
    @pytest.mark.asyncio
    async def test_approve_reviewing_req_to_drafting_spec(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_approve_reviewing_spec_to_drafting_tests(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_spec"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="specification",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_spec"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_approve_reviewing_tests_to_approved(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_tests"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="test_case",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(
            another_user.id, permissions=["requirement:review_tests"]
        )
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_reject_reviewing_req_to_drafting_req(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": "描述不清晰"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_reject_reviewing_spec_to_drafting_spec(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_spec"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="specification",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_spec"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": "API设计有误"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_reject_reviewing_tests_to_drafting_tests(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_tests"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="test_case",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(
            another_user.id, permissions=["requirement:review_tests"]
        )
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": "用例不完整"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_reject_without_comment_forbidden(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "reject", "comment": ""},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40302

    @pytest.mark.asyncio
    async def test_review_not_designated_reviewer_forbidden(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40301

    @pytest.mark.asyncio
    async def test_review_already_processed(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from datetime import datetime, timezone

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="approved",
            reviewed_at=datetime.now(timezone.utc),
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40303

    @pytest.mark.asyncio
    async def test_review_permission_mismatch(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        from app.models import RequirementReview

        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=another_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(
            another_user.id, permissions=["requirement:review_spec"]
        )
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestRequirementPrototypeHtml:
    @pytest.mark.asyncio
    async def test_create_requirement_with_prototype_html(
        self, client, normal_user, sample_iteration
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:create"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/requirements",
            json={
                "title": "带原型图的需求",
                "req_type": "feature",
                "priority": 3,
                "description": "测试",
                "prototype_html": "<div><h1>登录页</h1><button>提交</button></div>",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["prototype_html"] == "<div><h1>登录页</h1><button>提交</button></div>"

    @pytest.mark.asyncio
    async def test_update_requirement_prototype_html(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={
                "prototype_html": "<div><h2>更新后的原型</h2></div>",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["prototype_html"] == "<div><h2>更新后的原型</h2></div>"

    @pytest.mark.asyncio
    async def test_get_requirement_includes_prototype_html(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"prototype_html": "<button>测试</button>"},
            headers=headers,
        )

        headers = auth_headers(normal_user.id, permissions=["requirement:read"])
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["prototype_html"] == "<button>测试</button>"

    @pytest.mark.asyncio
    async def test_patch_requirement_prototype_html(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"prototype_html": "<div>patched</div>"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0


class TestRequirementStatusTransitionSecurity:
    @pytest.mark.asyncio
    async def test_patch_cannot_edit_title_in_reviewing_status(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "reviewing_req"},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] != 0

    @pytest.mark.asyncio
    async def test_patch_cannot_jump_to_approved(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "approved"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] != 0

    @pytest.mark.asyncio
    async def test_patch_can_edit_in_drafting_req(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "new title"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_patch_valid_transition_to_reviewing(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "reviewing_req"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "reviewing_req"

    @pytest.mark.asyncio
    async def test_patch_reject_then_re_edit(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "reviewing_req"},
            headers=headers,
        )
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "drafting_req"},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "revised title"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0


class TestPatchRequirementTypeDetailPath:
    @pytest.mark.asyncio
    async def test_type_detail_path_partial_update(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        sample_requirement.type_detail = {"severity": "low", "reproduce_steps": ["old"]}
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail_path": "reproduce_steps", "value": ["step1", "step2"]},
            headers=headers,
        )
        assert resp.json()["code"] == 0
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=auth_headers(normal_user.id),
        )
        td = get_resp.json()["data"]["type_detail"]
        assert td["severity"] == "low"
        assert td["reproduce_steps"] == ["step1", "step2"]

    @pytest.mark.asyncio
    async def test_type_detail_path_and_type_detail_mutually_exclusive(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail": {"a": 1}, "type_detail_path": "a", "value": 2},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001
        assert "type_detail_path" in body["message"]

    @pytest.mark.asyncio
    async def test_type_detail_path_not_found_actionable(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        sample_requirement.type_detail = {"severity": "low"}
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail_path": "nonexistent", "value": 1},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "severity" in body["message"]

    @pytest.mark.asyncio
    async def test_patch_prototype_html(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"prototype_html": "<div>proto</div>"},
            headers=headers,
        )
        assert resp.json()["code"] == 0
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=auth_headers(normal_user.id),
        )
        assert get_resp.json()["data"]["prototype_html"] == "<div>proto</div>"
