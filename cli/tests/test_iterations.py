from unittest.mock import patch

from sdd_cli.main import app


class TestIterationsList:
    def test_list_iterations(self, runner, mock_client):
        mock_client.get.return_value = [{"id": 1, "name": "Sprint 1"}]
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "list", "--project", "1"])
        assert result.exit_code == 0
        assert "Sprint 1" in result.output
        mock_client.get.assert_called_with("/projects/1/iterations", params={})

    def test_list_iterations_with_status(self, runner, mock_client):
        mock_client.get.return_value = [{"id": 1, "name": "Sprint 1"}]
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["iterations", "list", "--project", "1", "--status", "active"]
            )
        assert result.exit_code == 0
        mock_client.get.assert_called_with(
            "/projects/1/iterations", params={"status": "active"}
        )


class TestIterationsGet:
    def test_get_iteration(self, runner, mock_client):
        mock_client.get.return_value = {"id": 1, "name": "Sprint 1"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "get", "1"])
        assert result.exit_code == 0
        assert "Sprint 1" in result.output
        mock_client.get.assert_called_with("/iterations/1")


class TestIterationsCreate:
    def test_create_iteration_with_project(self, runner, mock_client):
        mock_client.post.return_value = {"id": 2, "name": "Sprint 2"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "iterations", "create",
                    "--name", "Sprint 2",
                    "--project", "1",
                    "--goal", "Ship feature",
                    "--start-date", "2024-01-01",
                    "--end-date", "2024-01-14",
                ],
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/projects/1/iterations",
            json={
                "name": "Sprint 2",
                "goal": "Ship feature",
                "start_date": "2024-01-01",
                "end_date": "2024-01-14",
            },
        )

    def test_create_iteration_without_project(self, runner, mock_client):
        mock_client.post.return_value = {"id": 3, "name": "Standalone"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "iterations", "create",
                    "--name", "Standalone",
                    "--start-date", "2024-02-01",
                    "--end-date", "2024-02-14",
                ],
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/iterations",
            json={
                "name": "Standalone",
                "start_date": "2024-02-01",
                "end_date": "2024-02-14",
            },
        )


class TestIterationsUpdate:
    def test_update_iteration(self, runner, mock_client):
        mock_client.put.return_value = {"id": 1, "name": "Updated Sprint"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["iterations", "update", "1", "--name", "Updated Sprint"]
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/iterations/1", json={"name": "Updated Sprint"}
        )

    def test_update_iteration_multiple_fields(self, runner, mock_client):
        mock_client.put.return_value = {"id": 1, "name": "Updated"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "iterations", "update", "1",
                    "--name", "Updated",
                    "--goal", "New goal",
                    "--start-date", "2024-03-01",
                    "--end-date", "2024-03-14",
                ],
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/iterations/1",
            json={
                "name": "Updated",
                "goal": "New goal",
                "start_date": "2024-03-01",
                "end_date": "2024-03-14",
            },
        )


class TestIterationsStart:
    def test_start_iteration(self, runner, mock_client):
        mock_client.post.return_value = {"id": 1, "status": "active"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "start", "1"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/iterations/1/start")


class TestIterationsComplete:
    def test_complete_iteration(self, runner, mock_client):
        mock_client.post.return_value = {"id": 1, "status": "completed"}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "complete", "1"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/iterations/1/complete")


class TestIterationsKanban:
    def test_kanban(self, runner, mock_client):
        mock_client.get.return_value = {"columns": [], "tasks": []}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "kanban", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/iterations/1/kanban")


class TestIterationsStatistics:
    def test_statistics(self, runner, mock_client):
        mock_client.get.return_value = {"total_tasks": 10, "completed": 7}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "statistics", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/iterations/1/statistics")

    def test_test_stats(self, runner, mock_client):
        mock_client.get.return_value = {"total": 20, "passed": 18}
        with patch("sdd_cli.iterations.get_client", return_value=mock_client):
            result = runner.invoke(app, ["iterations", "test-stats", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/iterations/1/test-statistics")
