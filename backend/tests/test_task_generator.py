import pytest
from tests.conftest import auth_headers


@pytest.fixture
async def setup_approved_requirement_with_spec(client, normal_user):
    headers = auth_headers(normal_user.id)

    resp = await client.post(
        "/api/v1/requirements",
        json={"title": "gen task test", "type": "feature", "priority": 2, "description": "test"},
        headers=headers,
    )
    req_id = resp.json()["data"]["id"]

    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "reviewing_req"}, headers=headers)
    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_spec"}, headers=headers)

    await client.put(
        f"/api/v1/requirements/{req_id}/specification",
        json={"content": {
            "page_structure": {
                "pages": [
                    {
                        "name": "登录页面",
                        "code": "login-page",
                        "route": "/login",
                        "elements": [
                            {"code": "btn-login", "type": "button", "label": "登录", "role": "button", "accessible_name": "登录", "interaction": "提交表单"}
                        ],
                        "interactions": [
                            {"trigger": "btn-login click", "behavior": "提交登录表单"}
                        ]
                    }
                ]
            },
            "api_design": {
                "endpoints": [
                    {"method": "POST", "path": "/api/v1/auth/login", "description": "登录接口"}
                ]
            }
        }},
        headers=headers,
    )

    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "reviewing_spec"}, headers=headers)
    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_tests"}, headers=headers)
    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "reviewing_tests"}, headers=headers)
    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "approved"}, headers=headers)

    return req_id


class TestTaskGenerator:
    @pytest.mark.asyncio
    async def test_generate_tasks_hybrid(self, client, normal_user, setup_approved_requirement_with_spec):
        req_id = setup_approved_requirement_with_spec
        headers = auth_headers(normal_user.id)

        resp = await client.post(f"/api/v1/requirements/{req_id}/generate-tasks", json={"strategy": "hybrid"}, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]["created"]) >= 2
        task_types = [t["task_type"] for t in body["data"]["created"]]
        assert "frontend" in task_types

    @pytest.mark.asyncio
    async def test_generate_tasks_not_approved(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.post(
            "/api/v1/requirements",
            json={"title": "not approved", "type": "feature", "priority": 1, "description": "test"},
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        resp2 = await client.post(f"/api/v1/requirements/{req_id}/generate-tasks", json={"strategy": "hybrid"}, headers=headers)
        body = resp2.json()
        assert body["code"] != 0
