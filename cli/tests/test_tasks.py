from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdd_cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestTasksGet:
    def test_get(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"id": 1, "title": "Task A", "status": "coding"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "get", "1"])
        assert result.exit_code == 0


class TestTasksCreate:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "title": "New Task"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "create", "--requirement", "10", "--title", "New Task"])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["requirement_id"] == 10

    def test_create_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 3}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "tasks", "create", "--requirement", "10", "--title", "Full",
                "--description", "Do things", "--assignee", "5",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["assignee_id"] == 5


class TestTasksUpdate:
    def test_update(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1, "title": "Updated"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "update", "1", "--title", "Updated", "--assignee", "3"])
        assert result.exit_code == 0


class TestTasksDelete:
    def test_delete(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"id": 1}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "delete", "1"])
        assert result.exit_code == 0


class TestTasksPatch:
    def test_patch_status(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"id": 1, "status": "coding"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "patch", "1", "--status", "coding"])
        assert result.exit_code == 0

    def test_patch_error(self, runner: CliRunner, mock_client: MagicMock) -> None:
        from sdd_cli.client import APIError
        mock_client.patch.side_effect = APIError(40001, "不允许转换")
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "patch", "1", "--status", "coding"])
        assert result.exit_code == 1


class TestTasksStartCoding:
    def test_start_coding(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "coding"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "start-coding", "1"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/tasks/1/start-coding")


class TestTasksStartTesting:
    def test_start_testing(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "testing"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "start-testing", "1"])
        assert result.exit_code == 0


class TestTasksComplete:
    def test_complete(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "completed"}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "complete", "1"])
        assert result.exit_code == 0


class TestTasksGitInfo:
    def test_branch_only(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"id": 1}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "git-info", "1", "--branch", "feat/1"])
        assert result.exit_code == 0
        mock_client.patch.assert_called_with("/tasks/1/git-info", json={"git_branch": "feat/1"})

    def test_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"id": 1}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "tasks", "git-info", "1",
                "--branch", "feat/1", "--sha", "abc123",
                "--pr", "http://pr/1", "--artifact", "http://art/1",
            ])
        assert result.exit_code == 0
        body = mock_client.patch.call_args[1]["json"]
        assert body["git_branch"] == "feat/1"
        assert body["commit_sha"] == "abc123"
        assert body["pr_url"] == "http://pr/1"


class TestTasksTestExecutions:
    def test_get(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = [{"id": 1}]
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, ["tasks", "test-executions", "1"])
        assert result.exit_code == 0


class TestTasksCreateTestRecord:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "passed", "round_id": 5}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "tasks", "create-test-record", "1",
                "--test-case-id", "10", "--status", "passed", "--actual-result", "OK",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["test_case_id"] == 10
        assert body["status"] == "passed"


class TestTasksCreateTestRound:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 6, "round_id": 6}
        with patch("sdd_cli.tasks.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "tasks", "create-test-round", "1",
                "--test-case-id", "10", "--status", "failed", "--failure-reason", "Null pointer",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["failure_reason"] == "Null pointer"
