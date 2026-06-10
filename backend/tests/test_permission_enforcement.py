import pytest
from tests.conftest import auth_headers


class TestRequirementPatchPermission:
    @pytest.mark.asyncio
    async def test_patch_requirement_no_team_member_forbidden(
        self, client, another_user, sample_requirement
    ):
        headers = auth_headers(another_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_patch_requirement_member_wrong_permission_forbidden(
        self, client, another_user, sample_requirement, owner_role, db
    ):
        from app.models import TeamMember, MemberRole, Role, RolePermission

        team = owner_role["team"]
        member = TeamMember(team_id=team.id, user_id=another_user.id)
        db.add(member)
        await db.flush()
        role = Role(team_id=team.id, name="只能创建", is_builtin=False)
        db.add(role)
        await db.flush()
        db.add(RolePermission(role_id=role.id, permission="requirement:create"))
        await db.flush()
        db.add(MemberRole(member_id=member.id, role_id=role.id))
        await db.commit()

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestApproveDirectPermission:
    @pytest.mark.asyncio
    async def test_approve_reviewing_req_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_req"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/approve",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_approve_reviewing_spec_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_spec"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/approve",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_approve_reviewing_tests_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_tests"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_tests"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/approve",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_approve_member_wrong_permission_forbidden(
        self, client, another_user, sample_requirement, owner_role, db
    ):
        from app.models import TeamMember, MemberRole, Role, RolePermission

        sample_requirement.status = "reviewing_req"
        db.add(sample_requirement)
        await db.flush()

        team = owner_role["team"]
        member = TeamMember(team_id=team.id, user_id=another_user.id)
        db.add(member)
        await db.flush()
        role = Role(team_id=team.id, name="只能评审规范", is_builtin=False)
        db.add(role)
        await db.flush()
        db.add(RolePermission(role_id=role.id, permission="requirement:review_spec"))
        await db.flush()
        db.add(MemberRole(member_id=member.id, role_id=role.id))
        await db.commit()

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/approve",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestApproveSpecDirectPermission:
    @pytest.mark.asyncio
    async def test_approve_spec_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["requirement:review_spec"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/approve-spec",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestSpecificationEditPermission:
    @pytest.mark.asyncio
    async def test_update_specification_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["specification:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {"text": "hacked spec"}},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_save_spec_direct_no_team_member_forbidden(
        self, client, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(another_user.id, permissions=["specification:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/spec",
            json={"content": {"text": "hacked spec"}},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_update_specification_member_wrong_permission_forbidden(
        self, client, another_user, sample_requirement, owner_role, db
    ):
        from app.models import TeamMember, MemberRole, Role, RolePermission

        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.flush()

        team = owner_role["team"]
        member = TeamMember(team_id=team.id, user_id=another_user.id)
        db.add(member)
        await db.flush()
        role = Role(team_id=team.id, name="只能编辑需求", is_builtin=False)
        db.add(role)
        await db.flush()
        db.add(RolePermission(role_id=role.id, permission="requirement:edit"))
        await db.flush()
        db.add(MemberRole(member_id=member.id, role_id=role.id))
        await db.commit()

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {"text": "hacked spec"}},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestGenerateTasksPermission:
    @pytest.mark.asyncio
    async def test_generate_tasks_no_team_member_forbidden(
        self, client, another_user, sample_requirement
    ):
        headers = auth_headers(another_user.id, permissions=["task:create"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/generate-tasks",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestReviewPermissionEnforcement:
    @pytest.mark.asyncio
    async def test_review_without_permission_forbidden(
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

        headers = auth_headers(another_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/review",
            json={"action": "approve"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestTaskPermissionEnforcement:
    @pytest.mark.asyncio
    async def test_patch_task_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:edit"])
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_update_task_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:edit"])
        resp = await client.put(
            f"/api/v1/tasks/{sample_task.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_delete_task_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:delete"])
        resp = await client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_complete_task_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:complete"])
        resp = await client.post(
            f"/api/v1/tasks/{sample_task.id}/complete",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_start_testing_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:test"])
        resp = await client.post(
            f"/api/v1/tasks/{sample_task.id}/start-testing",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_start_coding_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:edit"])
        resp = await client.post(
            f"/api/v1/tasks/{sample_task.id}/start-coding",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_update_git_info_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:edit"])
        resp = await client.patch(
            f"/api/v1/tasks/{sample_task.id}/git-info",
            json={"git_branch": "hacked"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_create_test_record_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:test"])
        resp = await client.post(
            f"/api/v1/tasks/{sample_task.id}/test-records",
            json={"test_case_id": 1, "status": "passed"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_create_test_round_no_team_member_forbidden(
        self, client, another_user, sample_task
    ):
        headers = auth_headers(another_user.id, permissions=["task:test"])
        resp = await client.post(
            f"/api/v1/tasks/{sample_task.id}/test-rounds",
            json={"test_case_id": 1, "status": "passed"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300
