import pytest
from tests.conftest import auth_headers


class TestListIterations:
    @pytest.mark.asyncio
    async def test_list_iterations_success(self, client, normal_user, sample_project, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/projects/{sample_project.id}/iterations",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1
        item = body["data"][0]
        assert item["id"] == sample_iteration.id
        assert "requirement_count" in item
        assert "task_count" in item

    @pytest.mark.asyncio
    async def test_list_iterations_filter_by_status(self, client, normal_user, sample_project, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/projects/{sample_project.id}/iterations?status=planned",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert all(i["status"] == "planned" for i in body["data"])

    @pytest.mark.asyncio
    async def test_list_iterations_non_member_forbidden(self, client, another_user, sample_project):
        headers = auth_headers(another_user.id)
        resp = await client.get(
            f"/api/v1/projects/{sample_project.id}/iterations",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestCreateIteration:
    @pytest.mark.asyncio
    async def test_create_iteration_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["iteration:create"])
        resp = await client.post(
            f"/api/v1/projects/{sample_project.id}/iterations",
            json={"name": "Sprint 1", "goal": "目标", "start_date": "2026-05-01", "end_date": "2026-05-31"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "id" in body["data"]

    @pytest.mark.asyncio
    async def test_create_iteration_end_date_before_start_date(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["iteration:create"])
        resp = await client.post(
            f"/api/v1/projects/{sample_project.id}/iterations",
            json={"name": "Sprint Bad", "goal": "目标", "start_date": "2026-06-01", "end_date": "2026-05-01"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_iteration_missing_name(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["iteration:create"])
        resp = await client.post(
            f"/api/v1/projects/{sample_project.id}/iterations",
            json={"name": "", "goal": "目标", "start_date": "2026-05-01", "end_date": "2026-05-31"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_iteration_no_permission(self, client, normal_user, another_user, sample_project):
        headers = auth_headers(another_user.id)
        resp = await client.post(
            f"/api/v1/projects/{sample_project.id}/iterations",
            json={"name": "Sprint No", "goal": "目标", "start_date": "2026-05-01", "end_date": "2026-05-31"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestGetIterationDetail:
    @pytest.mark.asyncio
    async def test_get_iteration_success(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/iterations/{sample_iteration.id}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["id"] == sample_iteration.id
        assert "project" in data
        assert data["project"]["id"] is not None
        assert "statistics" in data
        stats = data["statistics"]
        assert "total_requirements" in stats
        assert "approved_requirements" in stats
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "test_pass_rate" in stats

    @pytest.mark.asyncio
    async def test_get_iteration_not_found(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/iterations/99999", headers=headers)
        body = resp.json()
        assert body["code"] == 40400


class TestUpdateIteration:
    @pytest.mark.asyncio
    async def test_update_iteration_success(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id, permissions=["iteration:edit"])
        resp = await client.put(
            f"/api/v1/iterations/{sample_iteration.id}",
            json={"name": "Sprint 1v2", "goal": "新目标", "end_date": "2026-06-15"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_update_iteration_cannot_change_start_date(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id, permissions=["iteration:edit"])
        resp = await client.put(
            f"/api/v1/iterations/{sample_iteration.id}",
            json={"start_date": "2026-06-01"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40100

    @pytest.mark.asyncio
    async def test_update_iteration_completed_forbidden(self, client, normal_user, sample_iteration, db):
        sample_iteration.status = "completed"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:edit"])
        resp = await client.put(
            f"/api/v1/iterations/{sample_iteration.id}",
            json={"name": "尝试修改已完成迭代"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204


class TestStartIteration:
    @pytest.mark.asyncio
    async def test_start_iteration_success(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id, permissions=["iteration:start"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/start",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_start_iteration_already_in_progress(self, client, normal_user, sample_iteration, db):
        sample_iteration.status = "in_progress"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:start"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/start",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_start_iteration_already_completed(self, client, normal_user, sample_iteration, db):
        sample_iteration.status = "completed"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:start"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/start",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_start_iteration_no_permission(self, client, normal_user, another_user, sample_iteration):
        headers = auth_headers(another_user.id)
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/start",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestCompleteIteration:
    @pytest.mark.asyncio
    async def test_complete_iteration_success(self, client, normal_user, sample_iteration, db):
        sample_iteration.status = "in_progress"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:complete"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/complete",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_complete_iteration_uncompleted_requirements(self, client, normal_user, sample_iteration, sample_requirement, db):
        sample_iteration.status = "in_progress"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:complete"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/complete",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40200

    @pytest.mark.asyncio
    async def test_complete_iteration_uncompleted_tasks(self, client, normal_user, sample_iteration, approved_requirement, sample_task, db):
        sample_iteration.status = "in_progress"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:complete"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/complete",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40201

    @pytest.mark.asyncio
    async def test_complete_iteration_unpassed_tests(self, client, normal_user, sample_iteration, approved_requirement, sample_task, db):
        sample_iteration.status = "in_progress"
        sample_task.status = "completed"
        db.add_all([sample_iteration, sample_task])
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["iteration:complete"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/complete",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40202

    @pytest.mark.asyncio
    async def test_complete_iteration_not_in_progress(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id, permissions=["iteration:complete"])
        resp = await client.post(
            f"/api/v1/iterations/{sample_iteration.id}/complete",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204


class TestIterationKanban:
    @pytest.mark.asyncio
    async def test_kanban_success(self, client, normal_user, sample_iteration, sample_requirement):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/kanban",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        columns = body["data"]["columns"]
        assert isinstance(columns, list)
        assert len(columns) > 0
        col = columns[0]
        assert "status" in col
        assert "display_name" in col
        assert "requirements" in col

    @pytest.mark.asyncio
    async def test_kanban_display_name_mapping(self, client, normal_user, sample_iteration, sample_requirement):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/kanban",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        columns = body["data"]["columns"]
        status_to_name = {c["status"]: c["display_name"] for c in columns}
        assert status_to_name.get("drafting_req") == "编写需求"
        assert status_to_name.get("reviewing_req") == "需求审核中"
        assert status_to_name.get("drafting_spec") == "编写规范"
        assert status_to_name.get("reviewing_spec") == "规范审核中"
        assert status_to_name.get("drafting_tests") == "编写测试用例"
        assert status_to_name.get("reviewing_tests") == "测试用例审核中"
        assert status_to_name.get("approved") == "已通过"

    @pytest.mark.asyncio
    async def test_kanban_empty_iteration(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/kanban",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        for col in body["data"]["columns"]:
            assert col["requirements"] == []


class TestIterationStatistics:
    @pytest.mark.asyncio
    async def test_statistics_success(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/statistics",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert "requirements" in data
        assert "tasks" in data
        assert "tests" in data
        assert "total" in data["requirements"]
        assert "by_status" in data["requirements"]
        assert "total" in data["tasks"]
        assert "completed" in data["tasks"]
        assert "total_cases" in data["tests"]
        assert "latest_pass_rate" in data["tests"]


class TestIterationTestStatistics:
    @pytest.mark.asyncio
    async def test_test_statistics_success(self, client, normal_user, sample_iteration):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/iterations/{sample_iteration.id}/test-statistics",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "data" in body
