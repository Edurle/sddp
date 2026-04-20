import pytest
from tests.conftest import auth_headers


class TestListTeamProjects:
    @pytest.mark.asyncio
    async def test_list_projects_success(self, client, normal_user, owner_role, sample_project):
        headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/teams/{owner_role['team'].id}/projects", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
        assert len(body["data"]) >= 1
        project = body["data"][0]
        assert project["id"] == sample_project.id
        assert "active_iteration" in project

    @pytest.mark.asyncio
    async def test_list_projects_filter_active(self, client, normal_user, owner_role, sample_project):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/teams/{owner_role['team'].id}/projects?status=active",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert all(p["status"] == "active" for p in body["data"])

    @pytest.mark.asyncio
    async def test_list_projects_filter_archived(self, client, normal_user, owner_role, db):
        from app.models import Project

        project = Project(
            team_id=owner_role["team"].id,
            name="已归档项目",
            status="archived",
        )
        db.add(project)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/teams/{owner_role['team'].id}/projects?status=archived",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert all(p["status"] == "archived" for p in body["data"])

    @pytest.mark.asyncio
    async def test_list_projects_non_member_forbidden(self, client, normal_user, another_user, owner_role):
        headers = auth_headers(another_user.id)
        resp = await client.get(f"/api/v1/teams/{owner_role['team'].id}/projects", headers=headers)
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_list_projects_not_logged_in(self, client, owner_role):
        resp = await client.get(f"/api/v1/teams/{owner_role['team'].id}/projects")
        body = resp.json()
        assert body["code"] == 40100


class TestCreateProject:
    @pytest.mark.asyncio
    async def test_create_project_success(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=["project:create"])
        resp = await client.post(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            json={"name": "项目A", "description": "描述", "start_date": "2026-04-01"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "id" in body["data"]

    @pytest.mark.asyncio
    async def test_create_project_without_start_date(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=["project:create"])
        resp = await client.post(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            json={"name": "项目B", "description": "无开始日期"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_create_project_missing_name(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=["project:create"])
        resp = await client.post(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            json={"name": "", "description": "描述"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_create_project_no_permission(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.post(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            json={"name": "项目C", "description": "描述"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_create_project_not_logged_in(self, client, owner_role):
        resp = await client.post(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            json={"name": "项目D", "description": "描述"},
        )
        body = resp.json()
        assert body["code"] == 40100


class TestGetProjectDetail:
    @pytest.mark.asyncio
    async def test_get_project_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/projects/{sample_project.id}", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["id"] == sample_project.id
        assert "team" in data
        assert "statistics" in data
        stats = data["statistics"]
        assert "total_requirements" in stats
        assert "completed_requirements" in stats
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "test_pass_rate" in stats

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/projects/99999", headers=headers)
        body = resp.json()
        assert body["code"] == 40400

    @pytest.mark.asyncio
    async def test_get_project_non_member_forbidden(self, client, another_user, sample_project):
        headers = auth_headers(another_user.id)
        resp = await client.get(f"/api/v1/projects/{sample_project.id}", headers=headers)
        body = resp.json()
        assert body["code"] == 40300


class TestUpdateProject:
    @pytest.mark.asyncio
    async def test_update_project_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["project:edit"])
        resp = await client.put(
            f"/api/v1/projects/{sample_project.id}",
            json={"name": "新名称", "description": "新描述", "start_date": "2026-05-01"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_update_project_no_permission(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.put(
            f"/api/v1/projects/{sample_project.id}",
            json={"name": "尝试更新"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, client, normal_user):
        headers = auth_headers(normal_user.id, permissions=["project:edit"])
        resp = await client.put(
            "/api/v1/projects/99999",
            json={"name": "不存在"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400


class TestArchiveProject:
    @pytest.mark.asyncio
    async def test_archive_project_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["project:archive"])
        resp = await client.put(
            f"/api/v1/projects/{sample_project.id}/archive",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_archive_project_verify_status(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["project:archive"])
        await client.put(f"/api/v1/projects/{sample_project.id}/archive", headers=headers)

        detail_headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/projects/{sample_project.id}", headers=detail_headers)
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "archived"

    @pytest.mark.asyncio
    async def test_archive_project_already_archived(self, client, normal_user, sample_project, db):
        sample_project.status = "archived"
        db.add(sample_project)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["project:archive"])
        resp = await client.put(
            f"/api/v1/projects/{sample_project.id}/archive",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_archive_project_no_permission(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.put(
            f"/api/v1/projects/{sample_project.id}/archive",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestDeleteProject:
    @pytest.mark.asyncio
    async def test_delete_project_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=["project:delete"])
        resp = await client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_delete_project_with_active_iterations(self, client, normal_user, sample_project, sample_iteration, db):
        sample_iteration.status = "in_progress"
        db.add(sample_iteration)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["project:delete"])
        resp = await client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40203

    @pytest.mark.asyncio
    async def test_delete_project_not_in_list(self, client, normal_user, owner_role, sample_project):
        delete_headers = auth_headers(normal_user.id, permissions=["project:delete"])
        await client.delete(f"/api/v1/projects/{sample_project.id}", headers=delete_headers)

        list_headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/teams/{owner_role['team'].id}/projects",
            headers=list_headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert all(p["id"] != sample_project.id for p in body["data"])

    @pytest.mark.asyncio
    async def test_delete_project_no_permission(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id, permissions=[])
        resp = await client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestProjectTestStatistics:
    @pytest.mark.asyncio
    async def test_get_project_test_statistics_success(self, client, normal_user, sample_project):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/projects/{sample_project.id}/test-statistics",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "data" in body
