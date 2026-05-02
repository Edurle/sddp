from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdd_cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestTestExecutionsRecords:
    def test_get(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = [{"id": 1, "status": "passed"}]
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-executions", "records", "--round", "5"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/test-executions/5/records")


class TestTestExecutionsBatch:
    def test_batch(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"updated": 2}
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-executions", "batch", "--round", "5",
                "--records", '[{"test_case_id":1,"status":"passed"},{"test_case_id":2,"status":"failed","log_output":"err","duration_ms":120}]',
            ])
        assert result.exit_code == 0
        body = mock_client.put.call_args[1]["json"]
        assert len(body["records"]) == 2
        assert body["records"][1]["duration_ms"] == 120

    def test_batch_invalid_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-executions", "batch", "--round", "5", "--records", "bad"])
        assert result.exit_code == 1

    def test_batch_from_file(self, runner: CliRunner, mock_client: MagicMock, tmp_path) -> None:
        f = tmp_path / "records.json"
        f.write_text('[{"test_case_id":1,"status":"passed"}]')
        mock_client.put.return_value = {"updated": 1}
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-executions", "batch", "--round", "5", "--file", str(f)])
        assert result.exit_code == 0


class TestTestExecutionsUpdateRecord:
    def test_update(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1, "status": "passed"}
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, ["test-executions", "update-record", "1", "--status", "passed"])
        assert result.exit_code == 0

    def test_update_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1}
        with patch("sdd_cli.test_executions.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "test-executions", "update-record", "1",
                "--status", "failed", "--actual-result", "Error",
                "--failure-reason", "NPE", "--log-output", "trace",
                "--duration-ms", "350",
            ])
        assert result.exit_code == 0
        body = mock_client.put.call_args[1]["json"]
        assert body["status"] == "failed"
        assert body["log_output"] == "trace"
        assert body["duration_ms"] == 350
