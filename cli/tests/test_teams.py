from unittest.mock import patch

from sdd_cli.main import app


class TestTeamsGet:
    def test_get_team(self, runner, mock_client):
        mock_client.get.return_value = {"id": "t1", "name": "Team A"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "get", "t1"])
        assert result.exit_code == 0
        assert "Team A" in result.output
        mock_client.get.assert_called_with("/teams/t1")


class TestTeamsCreate:
    def test_create_team(self, runner, mock_client):
        mock_client.post.return_value = {"id": "t2", "name": "New Team"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "create", "--name", "New Team"])
        assert result.exit_code == 0
        assert "New Team" in result.output
        mock_client.post.assert_called_with(
            "/teams/", json={"name": "New Team"}
        )

    def test_create_team_with_description(self, runner, mock_client):
        mock_client.post.return_value = {"id": "t3", "name": "Team D"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["teams", "create", "--name", "Team D", "--description", "Desc"]
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/teams/", json={"name": "Team D", "description": "Desc"}
        )


class TestTeamsUpdate:
    def test_update_team(self, runner, mock_client):
        mock_client.put.return_value = {"id": "t1", "name": "Updated"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "update", "t1", "--name", "Updated"])
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/teams/t1", json={"name": "Updated"}
        )


class TestTeamsDelete:
    def test_delete_team(self, runner, mock_client):
        mock_client.delete.return_value = {"message": "deleted"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "delete", "t1", "--confirm"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/teams/t1")

    def test_delete_team_no_confirm(self, runner, mock_client):
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "delete", "t1"])
        assert result.exit_code == 1


class TestTeamsTransfer:
    def test_transfer_team(self, runner, mock_client):
        mock_client.post.return_value = {"id": "t1", "owner_id": "u2"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["teams", "transfer", "t1", "--new-owner-id", "u2"]
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/teams/t1/transfer", json={"new_owner_id": "u2"}
        )


class TestTeamsMembers:
    def test_list_members(self, runner, mock_client):
        mock_client.get.return_value = [
            {"user_id": "u1", "role": "admin"},
        ]
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "members", "t1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/teams/t1/members", params={})

    def test_list_members_with_role_filter(self, runner, mock_client):
        mock_client.get.return_value = [
            {"user_id": "u1", "role_id": 5},
        ]
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["teams", "members", "t1", "--role-id", "5"]
            )
        assert result.exit_code == 0
        mock_client.get.assert_called_with(
            "/teams/t1/members", params={"role_id": "5"}
        )


class TestTeamsInvite:
    def test_invite_member(self, runner, mock_client):
        mock_client.post.return_value = {"invitation_id": "inv1"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["teams", "invite", "t1", "--identifier", "user@example.com"]
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/teams/t1/invitations", json={"identifier": "user@example.com"}
        )


class TestTeamsRemoveMember:
    def test_remove_member(self, runner, mock_client):
        mock_client.delete.return_value = {"message": "removed"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "remove-member", "t1", "u1"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/teams/t1/members/u1")


class TestTeamsAssignRoles:
    def test_assign_roles(self, runner, mock_client):
        mock_client.put.return_value = {"user_id": "u1", "role_ids": [5, 6]}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app, ["teams", "assign-roles", "t1", "u1", "--role-ids", "5,6"]
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/teams/t1/members/u1/roles",
            json={"role_ids": [5, 6]},
        )


class TestTeamsRoles:
    def test_list_roles(self, runner, mock_client):
        mock_client.get.return_value = [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "member"},
        ]
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "roles", "t1"])
        assert result.exit_code == 0
        assert "admin" in result.output
        mock_client.get.assert_called_with("/teams/t1/roles")


class TestTeamsCreateRole:
    def test_create_role(self, runner, mock_client):
        mock_client.post.return_value = {"id": 3, "name": "editor"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "teams", "create-role", "t1",
                    "--name", "editor",
                    "--permissions", "read,write",
                ],
            )
        assert result.exit_code == 0
        mock_client.post.assert_called_with(
            "/teams/t1/roles",
            json={"name": "editor", "permissions": ["read", "write"]},
        )


class TestTeamsUpdateRole:
    def test_update_role(self, runner, mock_client):
        mock_client.put.return_value = {"id": 3, "name": "editor-v2"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                [
                    "teams", "update-role", "t1", "3",
                    "--name", "editor-v2",
                    "--permissions", "read",
                ],
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/teams/t1/roles/3",
            json={"name": "editor-v2", "permissions": ["read"]},
        )


class TestTeamsDeleteRole:
    def test_delete_role(self, runner, mock_client):
        mock_client.delete.return_value = {"message": "deleted"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "delete-role", "t1", "3"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/teams/t1/roles/3")


class TestTeamsSpecTemplate:
    def test_get_spec_template(self, runner, mock_client):
        mock_client.get.return_value = {"template_id": "st1", "sections": []}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "spec-template", "t1"])
        assert result.exit_code == 0
        assert "st1" in result.output
        mock_client.get.assert_called_with("/teams/t1/spec-template")


class TestTeamsAgentGuide:
    def test_get_agent_guide(self, runner, mock_client):
        mock_client.get.return_value = {"guide": "agent guide content"}
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(app, ["teams", "agent-guide", "t1"])
        assert result.exit_code == 0
        assert "agent guide content" in result.output
        mock_client.get.assert_called_with("/teams/t1/spec-template/agent-guide")


class TestTeamsUpdateSpecTemplate:
    def test_update_spec_template(self, runner, mock_client):
        mock_client.put.return_value = {"updated": True}
        sections_json = '[{"name": "overview"}]'
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                ["teams", "update-spec-template", "t1", "--sections", sections_json],
            )
        assert result.exit_code == 0
        mock_client.put.assert_called_with(
            "/teams/t1/spec-template",
            json={"sections": [{"name": "overview"}]},
        )

    def test_update_spec_template_invalid_json(self, runner, mock_client):
        with patch("sdd_cli.teams.get_client", return_value=mock_client):
            result = runner.invoke(
                app,
                ["teams", "update-spec-template", "t1", "--sections", "not-json"],
            )
        assert result.exit_code == 1
