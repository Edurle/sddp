from unittest.mock import patch

from sdd_cli.main import app


class TestProjectsList:
    def test_list_projects(self, runner, mock_client):
        mock_client.get.return_value = [{"id": 1, "name": "Project A"}]
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "list", "--team", "1"])
        assert result.exit_code == 0
        assert "Project A" in result.output
        mock_client.get.assert_called_with("/teams/1/projects", params={})

    def test_list_projects_with_status(self, runner, mock_client):
        mock_client.get.return_value = [{"id": 1, "name": "Project A"}]
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["projects", "list", "--team", "1", "--status", "active"]
            )
        assert result.exit_code == 0
        mock_client.get.assert_called_with(
            "/teams/1/projects", params={"status": "active"}
        )


class TestProjectsGet:
    def test_get_project(self, runner, mock_client):
        mock_client.get.return_value = {"id": 1, "name": "Project A"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "get", "1"])
        assert result.exit_code == 0
        assert "Project A" in result.output
        mock_client.get.assert_called_with("/projects/1")


class TestProjectsCreate:
    def test_create_project(self, runner, mock_client):
        mock_client.post.return_value = {"id": 2, "name": "New Project"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["projects", "create", "--team", "1", "--name", "New Project"]
            )
        assert result.exit_code == 0
        assert "New Project" in result.output
        mock_client.post.assert_called_with(
            "/teams/1/projects", json={"name": "New Project"}
        )

    def test_create_project_with_all_options(self, runner, mock_client):
        mock_client.post.return_value = {"id": 3, "name": "Full Project"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "projects", "create",
                    "--team", "1",
                    "--name", "Full Project",
                    "--description", "A project",
                    "--start-date", "2024-01-01",
                ],
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/teams/1/projects",
            json={"name": "Full Project", "description": "A project", "start_date": "2024-01-01"},
        )


class TestProjectsUpdate:
    def test_update_project(self, runner, mock_client):
        mock_client.put.return_value = {"id": 1, "name": "Updated"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "update", "1", "--name", "Updated"])
        assert result.exit_code == 0
        mock_client.put.assert_called_with("/projects/1", json={"name": "Updated"})

    def test_update_project_multiple_fields(self, runner, mock_client):
        mock_client.put.return_value = {"id": 1, "name": "Updated"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "projects", "update", "1",
                    "--name", "Updated",
                    "--description", "New desc",
                    "--start-date", "2024-06-01",
                ],
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/projects/1",
            json={"name": "Updated", "description": "New desc", "start_date": "2024-06-01"},
        )


class TestProjectsArchive:
    def test_archive_project(self, runner, mock_client):
        mock_client.put.return_value = {"id": 1, "status": "archived"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "archive", "1"])
        assert result.exit_code == 0
        mock_client.put.assert_called_with("/projects/1/archive")


class TestProjectsDelete:
    def test_delete_project(self, runner, mock_client):
        mock_client.delete.return_value = {"message": "deleted"}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "delete", "1"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/projects/1")


class TestProjectsTestStats:
    def test_test_stats(self, runner, mock_client):
        mock_client.get.return_value = {"total": 50, "passed": 45}
        with patch("sdd_cli.projects.get_client", return_value=mock_client):
            result = runner.invoke(app, ["projects", "test-stats", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/projects/1/test-statistics")
