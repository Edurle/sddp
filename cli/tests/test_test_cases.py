from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdd_cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestTestCasesCreate:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "title": "TC1"}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "create", "--requirement", "10", "--title", "TC1", "--type", "functional",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["requirement_id"] == 10
        assert body["case_type"] == "functional"

    def test_create_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "create", "--requirement", "10", "--title", "TC2", "--type", "integration",
                "--precondition", "DB seeded", "--steps", "POST /api", "--expected", "200",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["precondition"] == "DB seeded"


class TestTestCasesUpdate:
    def test_update(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-cases", "update", "1", "--title", "Updated"])
        assert result.exit_code == 0


class TestTestCasesDelete:
    def test_delete(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"id": 1}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-cases", "delete", "1"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/test-cases/1")
