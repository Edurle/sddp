import pytest
from tests.conftest import auth_headers


class TestRequirementGuide:
    @pytest.mark.asyncio
    async def test_get_requirement_guide(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/requirements/guide", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

        data = body["data"]
        assert len(data["req_types"]) == 3
        assert data["req_types"][0]["value"] == "feature"
        assert len(data["priority_levels"]) == 3
        assert "required_fields" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_requirement_guide_unauthorized(self, client):
        resp = await client.get("/api/v1/requirements/guide")
        assert resp.status_code == 200
        body = resp.json()
        from app.exceptions import ERR_UNAUTHORIZED
        assert body["code"] == ERR_UNAUTHORIZED
