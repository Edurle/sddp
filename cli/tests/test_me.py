from unittest.mock import patch

from sdd_cli.client import APIError
from sdd_cli.main import app


class TestMeInfo:
    def test_me_success(self, runner, mock_client):
        mock_client.get.return_value = {
            "id": 1,
            "email": "me@example.com",
            "nickname": "meuser",
        }
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me"])
        assert result.exit_code == 0
        assert "me@example.com" in result.output


class TestMeTasks:
    def test_list_my_tasks(self, runner, mock_client):
        mock_client.get.return_value = [
            {"id": 1, "title": "Task A", "status": "in_progress"},
            {"id": 2, "title": "Task B", "status": "done"},
        ]
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "tasks"])
        assert result.exit_code == 0
        assert "Task A" in result.output

    def test_list_my_tasks_with_status(self, runner, mock_client):
        mock_client.get.return_value = [
            {"id": 1, "title": "Task A", "status": "in_progress"},
        ]
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "tasks", "-s", "in_progress"])
        assert result.exit_code == 0
        mock_client.get.assert_called_once_with(
            "/users/me/tasks",
            params={"limit": 50, "status": "in_progress"},
        )


class TestMePending:
    def test_pending_items(self, runner, mock_client):
        mock_client.get.return_value = [
            {"team_name": "Team A", "role": "member"},
        ]
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending"])
        assert result.exit_code == 0
        assert "Team A" in result.output


class TestMePendingReviews:
    def test_pending_reviews(self, runner, mock_client):
        mock_client.get.return_value = [
            {"review_id": 1, "title": "Review spec changes"},
        ]
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending-reviews"])
        assert result.exit_code == 0
        assert "Review spec changes" in result.output

    def test_no_pending_reviews(self, runner, mock_client):
        mock_client.get.return_value = []
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending-reviews"])
        assert result.exit_code == 0
