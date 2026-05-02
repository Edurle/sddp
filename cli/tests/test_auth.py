from unittest.mock import patch

from sdd_cli.client import APIError
from sdd_cli.main import app


class TestAuthLogin:
    def test_login_success(self, runner, mock_client):
        mock_client.post.return_value = {
            "access_token": "jwt-token-123",
            "user": {"email": "test@example.com", "id": 1},
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "login", "-e", "test@example.com", "-p", "secret"])
        assert result.exit_code == 0
        assert "jwt-token-123" in result.output

    def test_login_failure(self, runner, mock_client):
        mock_client.post.side_effect = APIError(code=40100, message="Invalid credentials")
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "login", "-e", "bad@example.com", "-p", "wrong"])
        assert result.exit_code == 1
        assert "Error: Invalid credentials" in result.output

    def test_login_missing_args(self, runner, mock_client):
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "login"])
        assert result.exit_code != 0


class TestAuthRegister:
    def test_register_success(self, runner, mock_client):
        mock_client.post.return_value = {
            "id": 2,
            "email": "new@example.com",
            "nickname": "newuser",
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "register", "-e", "new@example.com", "-p", "secret", "-n", "newuser"])
        assert result.exit_code == 0
        assert "new@example.com" in result.output


class TestAuthWhoami:
    def test_whoami_with_key(self, runner, mock_client):
        mock_client.get.return_value = {
            "id": 1,
            "email": "test@example.com",
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "whoami"])
        assert result.exit_code == 0
        assert "test@example.com" in result.output

    def test_whoami_no_key(self, runner, mock_client):
        mock_client.get.side_effect = APIError(code=40100, message="Not authenticated")
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "whoami"])
        assert result.exit_code == 1
        assert "Error: Not authenticated" in result.output


class TestAuthLogout:
    def test_logout(self, runner, mock_client):
        with patch("sdd_cli.auth.Config") as mock_config_cls:
            mock_cfg = mock_config_cls.load.return_value
            with patch("sdd_cli.auth.get_client", return_value=mock_client):
                result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Logged out" in result.output
        assert mock_cfg.api_key == ""
        mock_cfg.save.assert_called_once()
