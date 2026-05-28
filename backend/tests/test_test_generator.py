import pytest
from tests.conftest import auth_headers


@pytest.fixture
async def setup_requirement_for_tc(client, normal_user):
    headers = auth_headers(normal_user.id)

    resp = await client.post(
        "/api/v1/requirements",
        json={"title": "gen tc test", "type": "feature", "priority": 2, "description": "test"},
        headers=headers,
    )
    req_id = resp.json()["data"]["id"]

    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_spec"}, headers=headers)

    await client.put(
        f"/api/v1/requirements/{req_id}/specification",
        json={"content": {
            "page_structure": {
                "pages": [
                    {
                        "name": "登录页",
                        "code": "login",
                        "route": "/login",
                        "elements": [
                            {"code": "btn-login", "type": "button", "label": "登录", "accessible_name": "登录", "interaction": "提交登录表单"}
                        ]
                    }
                ]
            },
            "api_design": {
                "endpoints": [
                    {"method": "POST", "path": "/api/v1/auth/login", "description": "登录"}
                ]
            }
        }},
        headers=headers,
    )

    await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_tests"}, headers=headers)

    return req_id


class TestTestGenerator:
    @pytest.mark.asyncio
    async def test_generate_test_cases(self, client, normal_user, setup_requirement_for_tc):
        req_id = setup_requirement_for_tc
        headers = auth_headers(normal_user.id)

        resp = await client.post(f"/api/v1/requirements/{req_id}/generate-test-cases", json={"case_types": ["e2e", "api"]}, headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]["created"]) >= 2
        case_types = [c["case_type"] for c in body["data"]["created"]]
        assert "e2e" in case_types
        assert "api" in case_types

    @pytest.mark.asyncio
    async def test_generate_test_cases_wrong_status(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.post(
            "/api/v1/requirements",
            json={"title": "wrong status", "type": "feature", "priority": 1, "description": "test"},
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        resp2 = await client.post(f"/api/v1/requirements/{req_id}/generate-test-cases", json={}, headers=headers)
        body = resp2.json()
        assert body["code"] != 0
