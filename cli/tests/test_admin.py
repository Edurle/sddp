from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdd_cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestAdminUsers:
    def test_list(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [{"id": 1, "email": "a@b.com"}], "total": 1}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "users"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/admin/users", params={"page": 1, "page_size": 20, "search": ""})

    def test_list_with_search(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [], "total": 0}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "users", "--search", "alice"])
        assert result.exit_code == 0


class TestAdminCreateUser:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "email": "new@test.com"}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "admin", "create-user", "--email", "new@test.com", "--nickname", "New", "--password", "12345678",
            ])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/admin/users", json={"email": "new@test.com", "nickname": "New", "password": "12345678"})


class TestAdminToggleUser:
    def test_disable(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1, "is_active": False}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "toggle-user", "1", "--no-active"])
        assert result.exit_code == 0
        mock_client.put.assert_called_with("/admin/users/1/status", json={"is_active": False})

    def test_enable(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1, "is_active": True}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "toggle-user", "1", "--active"])
        assert result.exit_code == 0


class TestAdminCreateApiKey:
    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "id": 1, "name": "Key", "raw_key": "sdd_abc123", "key_prefix": "sdd_abc1", "user_id": 5,
        }
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "create-api-key", "--user", "5", "--name", "Key"])
        assert result.exit_code == 0
        assert "sdd_abc123" in result.output

    def test_create_with_expiry(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "raw_key": "sdd_xyz", "expires_at": "2026-12-31"}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "admin", "create-api-key", "--user", "5", "--name", "Temp", "--expires-at", "2026-12-31",
            ])
        assert result.exit_code == 0


class TestAdminListApiKeys:
    def test_list(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = [{"id": 1, "name": "Key A", "is_active": True}]
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "list-api-keys", "--user", "5"])
        assert result.exit_code == 0
        assert "Key A" in result.output


class TestAdminRevokeApiKey:
    def test_revoke(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"id": 1, "is_active": False}
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "revoke-api-key", "1"])
        assert result.exit_code == 0

    def test_revoke_not_found(self, runner: CliRunner, mock_client: MagicMock) -> None:
        from sdd_cli.client import APIError
        mock_client.delete.side_effect = APIError(40400, "不存在")
        with patch("sdd_cli.admin.get_client", return_value=mock_client):
            result = runner.invoke(app, ["admin", "revoke-api-key", "999"])
        assert result.exit_code == 1
