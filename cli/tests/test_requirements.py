from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sdd_cli.main import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestRequirementsList:
    def test_list_global(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "items": [{"id": 1, "title": "Req A", "status": "drafting_req"}],
            "total": 1,
            "offset": 0,
            "limit": 50,
            "has_more": False,
        }
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "list"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements", params={"offset": 0, "limit": 50})

    def test_list_with_filters(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [], "total": 0, "offset": 0, "limit": 10, "has_more": False}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "list", "--status", "drafting_req", "--iteration", "5", "--limit", "10"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements", params={"status": "drafting_req", "iteration_id": 5, "offset": 0, "limit": 10})


class TestRequirementsGet:
    def test_get(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"id": 1, "title": "Req A", "status": "drafting_req"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "get", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements/1")


class TestRequirementsCreate:
    def test_create_minimal(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "title": "New Req"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "create", "--title", "New Req"])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["title"] == "New Req"
        assert body["type"] == "feature"
        assert body["priority"] == 0
        assert "iteration_id" not in body

    def test_create_full(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 3, "title": "Full"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "create", "--title", "Full",
                "--type", "bugfix", "--priority", "3",
                "--description", "A bug", "--iteration", "10",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["type"] == "bugfix"
        assert body["priority"] == 3
        assert body["iteration_id"] == 10


class TestRequirementsUpdate:
    def test_update(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"id": 1, "title": "Updated"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "update", "1", "--title", "Updated"])
        assert result.exit_code == 0
        body = mock_client.put.call_args[1]["json"]
        assert body["title"] == "Updated"
        assert body["req_type"] is None


class TestRequirementsDelete:
    def test_delete(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"id": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "delete", "1"])
        assert result.exit_code == 0


class TestRequirementsPatch:
    def test_patch_status(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"id": 1, "status": "drafting_spec"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "patch", "1", "--status", "drafting_spec"])
        assert result.exit_code == 0
        body = mock_client.patch.call_args[1]["json"]
        assert body["status"] == "drafting_spec"


class TestRequirementsApprove:
    def test_approve(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "drafting_spec"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "approve", "1"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/approve")


class TestRequirementsFullContext:
    def test_full_context(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "requirement": {"id": 1, "title": "Req A"},
            "spec": {"current_version": 2},
            "tasks": [{"id": 1}],
            "test_cases": [{"id": 1}],
        }
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "full-context", "1"])
        assert result.exit_code == 0
        assert "Req A" in result.output


class TestRequirementsSubmitReview:
    def test_submit_review(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"review_id": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "submit-review", "1", "--reviewer", "5"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/submit-review", json={"reviewer_id": 5})


class TestRequirementsReview:
    def test_approve(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "review", "1", "--action", "approve"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/review", json={"action": "approve", "comment": None})

    def test_reject_with_comment(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "review", "1", "--action", "reject", "--comment", "Bad"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/review", json={"action": "reject", "comment": "Bad"})


class TestRequirementsTestStats:
    def test_test_stats(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"total_cases": 10, "passed": 8}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "test-stats", "1"])
        assert result.exit_code == 0


class TestRequirementsSpec:
    def test_get_spec(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"current_version": 2}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "spec", "1"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements/1/specification")

    def test_save_spec(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"current_version": 3}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "save-spec", "1", "--content", '{"entity_definition":{}}'])
        assert result.exit_code == 0
        mock_client.put.assert_called_with("/requirements/1/specification", json={"content": {"entity_definition": {}}})

    def test_save_spec_invalid_json(self, runner: CliRunner, mock_client: MagicMock) -> None:
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "save-spec", "1", "--content", "not-json"])
        assert result.exit_code == 1

    def test_save_spec_direct(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"version": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "save-spec-direct", "1", "--content", '{"text":"hi"}'])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/spec", json={"content": {"text": "hi"}})

    def test_spec_versions(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = [{"version": 1}, {"version": 2}]
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "spec-versions", "1"])
        assert result.exit_code == 0

    def test_spec_version(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"version": 2, "content": {}}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "spec-version", "1", "2"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements/1/specification/versions/2")


class TestRequirementsSpecWorkflow:
    def test_submit_spec_review(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"review_id": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "submit-spec-review", "1", "--reviewer", "5"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/submit-spec-review", json={"reviewer_id": 5})

    def test_approve_spec(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 1, "status": "drafting_tests"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "approve-spec", "1"])
        assert result.exit_code == 0

    def test_submit_tests_review(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"review_id": 2}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "submit-tests-review", "1", "--reviewer", "5"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/1/submit-tests-review", json={"reviewer_id": 5})


class TestRequirementsTestCases:
    def test_list(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [{"id": 1, "title": "TC1"}], "total": 1, "offset": 0, "limit": 50, "has_more": False}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "test-cases", "1"])
        assert result.exit_code == 0

    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "title": "TC New"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "create-test-case", "1",
                "--title", "TC New", "--type", "happy_path",
                "--precondition", "Logged in", "--steps", "Click",
                "--expected", "OK",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["title"] == "TC New"
        assert body["case_type"] == "happy_path"


class TestRequirementsTasks:
    def test_list(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [{"id": 1, "title": "T1"}], "total": 1, "offset": 0, "limit": 50, "has_more": False}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "tasks", "1"])
        assert result.exit_code == 0

    def test_list_with_filters(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"items": [], "total": 0, "offset": 0, "limit": 50, "has_more": False}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "tasks", "1", "--status", "coding", "--assignee", "3"])
        assert result.exit_code == 0
        mock_client.get.assert_called_with("/requirements/1/tasks", params={"status": "coding", "assignee_id": 3, "offset": 0, "limit": 50})

    def test_create(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"id": 2, "title": "New Task"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "create-task", "1",
                "--title", "New Task", "--description", "Do stuff",
            ])
        assert result.exit_code == 0
        body = mock_client.post.call_args[1]["json"]
        assert body["title"] == "New Task"
        assert body["description"] == "Do stuff"


class TestSetSpecField:
    def test_set_spec_field_reads_file(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path
    ) -> None:
        f = tmp_path / "desc.md"
        f.write_text("新描述", encoding="utf-8")
        mock_client.patch.return_value = {"is_draft": True, "base_version": 1}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "set-spec-field", "5",
                "entity_definition.description", "--file", str(f),
            ])
        assert result.exit_code == 0
        mock_client.patch.assert_called_with(
            "/requirements/5/specification/draft/field",
            json={"path": "entity_definition.description", "value": "新描述"},
        )


class TestCommitSpec:
    def test_commit_spec(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"version": 2}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "commit-spec", "5"])
        assert result.exit_code == 0
        mock_client.post.assert_called_with("/requirements/5/specification/commit")


class TestDiscardSpecDraft:
    def test_discard_spec_draft(self, runner: CliRunner, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"discarded": True}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, ["requirements", "discard-spec-draft", "5"])
        assert result.exit_code == 0
        mock_client.delete.assert_called_with("/requirements/5/specification/draft")


class TestReqSetField:
    def test_set_field_prototype_html(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path
    ) -> None:
        f = tmp_path / "proto.html"
        f.write_text("<div>x</div>", encoding="utf-8")
        mock_client.patch.return_value = {"id": 5, "status": "drafting_req"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "set-field", "5", "prototype_html",
                "--file", str(f),
            ])
        assert result.exit_code == 0
        mock_client.patch.assert_called_with(
            "/requirements/5", json={"prototype_html": "<div>x</div>"},
        )

    def test_set_field_type_detail_path(
        self, runner: CliRunner, mock_client: MagicMock, tmp_path
    ) -> None:
        import json as _json
        f = tmp_path / "steps.json"
        f.write_text(_json.dumps(["s1", "s2"]), encoding="utf-8")
        mock_client.patch.return_value = {"id": 5, "status": "drafting_req"}
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "set-field", "5", "type_detail.reproduce_steps",
                "--file", str(f),
            ])
        assert result.exit_code == 0
        mock_client.patch.assert_called_with(
            "/requirements/5",
            json={"type_detail_path": "reproduce_steps", "value": ["s1", "s2"]},
        )

    def test_set_field_unsupported_path(
        self, runner: CliRunner, mock_client: MagicMock
    ) -> None:
        with patch("sdd_cli.requirements.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "requirements", "set-field", "5", "unknown_field", "--file", "x",
            ])
        assert result.exit_code == 1
