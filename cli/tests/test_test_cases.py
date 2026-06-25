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
                "test-cases", "create", "--requirement", "10", "--title", "TC1", "--type", "happy_path",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["requirement_id"] == 10
        assert body["case_type"] == "happy_path"

    def test_create_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "create", "--requirement", "10", "--title", "TC2", "--type", "edge_case",
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


class TestTestCasesDeprecate:
    def test_deprecate(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "deprecated"}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-cases", "deprecate", "1"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/test-cases/1/deprecate")


class TestTestCasesSetField:
    def test_set_field_steps(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path
    ) -> None:
        f = tmp_path / "steps.txt"
        f.write_text("1. 步骤一\n2. 步骤二", encoding="utf-8")
        mock_client.put.return_value = {"id": 9}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "set-field", "9", "steps", "--file", str(f),
            ])
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/test-cases/9", json={"steps": "1. 步骤一\n2. 步骤二"},
        )

    def test_set_field_expected(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path
    ) -> None:
        f = tmp_path / "expected.md"
        f.write_text("预期结果", encoding="utf-8")
        mock_client.put.return_value = {"id": 9}
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "set-field", "9", "expected", "--file", str(f),
            ])
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/test-cases/9", json={"expected_result": "预期结果"},
        )

    def test_set_field_unsupported(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        with patch("sdd_cli.test_cases.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-cases", "set-field", "9", "badfield", "--file", "x",
            ])
        assert result.exit_code == 1
