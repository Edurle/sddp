import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_start_coding_pending_to_coding(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-coding", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "coding"


@pytest.mark.asyncio
async def test_start_coding_already_coding_fails(client, db, sample_task, normal_user):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-coding", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_start_coding_task_not_found(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post("/api/v1/tasks/99999/start-coding", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


@pytest.mark.asyncio
async def test_update_git_info_all_fields(client, db, sample_task, normal_user):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.patch(
        f"/api/v1/tasks/{sample_task.id}/git-info",
        json={
            "git_branch": "feature/test",
            "commit_sha": "abc123def456abc123def456abc123def456abcd",
            "pr_url": "https://github.com/test/pr/1",
            "artifact_url": "https://ci.example.com/build/42",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["git_branch"] == "feature/test"
    assert data["commit_sha"] == "abc123def456abc123def456abc123def456abcd"
    assert data["pr_url"] == "https://github.com/test/pr/1"
    assert data["artifact_url"] == "https://ci.example.com/build/42"


@pytest.mark.asyncio
async def test_update_git_info_partial(client, db, sample_task, normal_user):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.patch(
        f"/api/v1/tasks/{sample_task.id}/git-info",
        json={"commit_sha": "deadbeef"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["commit_sha"] == "deadbeef"


@pytest.mark.asyncio
async def test_update_git_info_task_not_found(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.patch(
        "/api/v1/tasks/99999/git-info",
        json={"git_branch": "main"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


@pytest.mark.asyncio
async def test_task_detail_includes_git_fields_when_set(client, db, sample_task, normal_user):
    sample_task.status = "coding"
    sample_task.git_branch = "feature/x"
    sample_task.commit_sha = "a1b2c3"
    sample_task.pr_url = "https://github.com/pr/99"
    sample_task.artifact_url = "https://ci.example.com/1"
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["git_branch"] == "feature/x"
    assert data["commit_sha"] == "a1b2c3"
    assert data["pr_url"] == "https://github.com/pr/99"
    assert data["artifact_url"] == "https://ci.example.com/1"


@pytest.mark.asyncio
async def test_task_detail_shows_null_git_fields_when_not_set(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["git_branch"] is None
    assert data["commit_sha"] is None
    assert data["pr_url"] is None
    assert data["artifact_url"] is None
