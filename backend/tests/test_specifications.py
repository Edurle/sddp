import pytest
from tests.conftest import auth_headers


class TestGetSpecTemplate:
    @pytest.mark.asyncio
    async def test_get_spec_template_success(
        self, client, normal_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/teams/{team.id}/spec-template",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert "sections" in data
        assert isinstance(data["sections"], list)
        if len(data["sections"]) > 0:
            section = data["sections"][0]
            assert "name" in section
            assert "display_name" in section
            assert "required" in section
            assert "fields" in section

    @pytest.mark.asyncio
    async def test_get_spec_template_new_team_has_default(
        self, client, normal_user, db
    ):
        from app.models import Team, TeamMember

        team = Team(name="全新团队", description="新创建", owner_id=normal_user.id)
        db.add(team)
        await db.flush()
        member = TeamMember(team_id=team.id, user_id=normal_user.id)
        db.add(member)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/teams/{team.id}/spec-template",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert "sections" in body["data"]

    @pytest.mark.asyncio
    async def test_get_spec_template_non_member_forbidden(
        self, client, another_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(another_user.id)
        resp = await client.get(
            f"/api/v1/teams/{team.id}/spec-template",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestUpdateSpecTemplate:
    @pytest.mark.asyncio
    async def test_update_spec_template_success(
        self, client, normal_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["spec_template:edit"])
        resp = await client.put(
            f"/api/v1/teams/{team.id}/spec-template",
            json={
                "sections": [
                    {
                        "name": "entity",
                        "display_name": "实体定义",
                        "required": True,
                        "fields": [
                            {
                                "name": "entities",
                                "display_name": "实体列表",
                                "type": "rich_text",
                                "required": True,
                                "description": "定义系统中的核心实体",
                            }
                        ],
                    }
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_update_spec_template_no_permission(
        self, client, normal_user, another_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(another_user.id)
        resp = await client.put(
            f"/api/v1/teams/{team.id}/spec-template",
            json={"sections": []},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300


class TestGetSpecDocument:
    @pytest.mark.asyncio
    async def test_get_spec_document_success(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert "current_version" in data
        assert "content" in data

    @pytest.mark.asyncio
    async def test_get_spec_document_no_spec_returns_empty(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data.get("current_version") is None or data.get("current_version") == 0
        assert data.get("content") is None or data.get("content") == {}

    @pytest.mark.asyncio
    async def test_get_spec_document_not_found(
        self, client, normal_user
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            "/api/v1/requirements/999/specification",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400


class TestSaveSpecDocument:
    @pytest.mark.asyncio
    async def test_save_spec_document_no_version_until_review(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        # 编辑不再生成版本：返回工作草稿标记，且版本列表仍为空。
        assert body["data"].get("is_draft") is True
        assert "version" not in body["data"]

        versions = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )
        assert versions.json()["data"] == []

    @pytest.mark.asyncio
    async def test_save_spec_document_multiple_saves_no_version(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])

        resp1 = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "v1", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        assert resp1.json()["code"] == 0

        resp2 = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "v2", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        assert resp2.json()["code"] == 0

        # 多次保存不产生任何版本；当前内容为最后一次保存。
        versions = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )
        assert versions.json()["data"] == []

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        assert get_resp.json()["data"]["content"]["entity_definition"]["description"] == "v2"

    @pytest.mark.asyncio
    async def test_save_spec_document_only_in_drafting_spec(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {},
                    "table_design": {},
                    "page_structure": {},
                    "api_design": {},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_save_spec_document_in_reviewing_spec_forbidden(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "reviewing_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {},
                    "table_design": {},
                    "page_structure": {},
                    "api_design": {},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_save_spec_document_in_approved_forbidden(
        self, client, normal_user, approved_requirement
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{approved_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {},
                    "table_design": {},
                    "page_structure": {},
                    "api_design": {},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_save_spec_document_after_rejection_back_to_drafting(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"].get("is_draft") is True


class TestListSpecVersions:
    @pytest.mark.asyncio
    async def test_list_spec_versions_success(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        # 先编辑（不产生版本），再通过规范审核 → 切出一个版本。
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT)},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )

        await _spec_review(client, db, sample_requirement, another_user, "approve")

        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 1
        item = body["data"][0]
        assert item["version"] == 1
        assert "created_by" in item
        assert "created_at" in item

    @pytest.mark.asyncio
    async def test_list_spec_versions_empty(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 0


class TestGetSpecVersionDetail:
    @pytest.mark.asyncio
    async def test_get_spec_version_detail_success(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT)},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        await _spec_review(client, db, sample_requirement, another_user, "approve")

        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions/1",
            headers=auth_headers(normal_user.id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert data["version"] == 1
        assert "content" in data
        assert "created_by" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_get_spec_version_not_found(
        self, client, normal_user, sample_requirement
    ):
        headers = auth_headers(normal_user.id)
        resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions/999",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40400


class TestSpecContentValidation:
    @pytest.mark.asyncio
    async def test_save_spec_missing_required_section(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        suggestions = body["data"].get("suggestions", [])
        assert any("api_design" in str(s) for s in suggestions)

    @pytest.mark.asyncio
    async def test_save_spec_missing_required_field_in_section(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        suggestions = body["data"].get("suggestions", [])
        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_save_spec_invalid_entity_fields_format(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test entity", "fields": "not_an_array"},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_save_spec_valid_content_passes_validation(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "用户实体",
                        "fields": [
                            {"name": "id", "type": "BIGINT", "constraints": ["PK"]},
                            {"name": "email", "type": "VARCHAR(255)", "constraints": ["NOT NULL"]},
                        ],
                    },
                    "table_design": {
                        "tables": [
                            {
                                "name": "users",
                                "fields": [
                                    {"name": "id", "type": "BIGINT"},
                                    {"name": "email", "type": "VARCHAR(255)"},
                                ],
                            }
                        ]
                    },
                    "page_structure": {
                        "pages": [
                            {
                                "name": "用户列表",
                                "code": "user-list",
                                "elements": [
                                    {"code": "user-btn-create", "type": "button", "label": "创建"},
                                ],
                            }
                        ]
                    },
                    "api_design": {
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/api/v1/users",
                                "description": "获取用户列表",
                            }
                        ]
                    },
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert "version" in body["data"]

    @pytest.mark.asyncio
    async def test_save_spec_with_prototype_html(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "test",
                        "fields": [{"name": "id", "type": "INT"}],
                    },
                    "table_design": {"tables": [{"name": "test", "fields": [{"name": "id", "type": "INT"}]}]},
                    "page_structure": {
                        "pages": [
                            {"name": "测试页", "code": "test-page", "elements": [{"code": "btn", "type": "button", "label": "按钮"}]}
                        ],
                    },
                    "api_design": {"endpoints": [{"method": "GET", "path": "/test", "description": "test"}]},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_save_spec_optional_constraints_section_can_be_omitted(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "test",
                        "fields": [{"name": "id", "type": "INT"}],
                    },
                    "table_design": {"tables": [{"name": "test", "fields": [{"name": "id", "type": "INT"}]}]},
                    "page_structure": {
                        "pages": [{"name": "test", "code": "test", "elements": [{"code": "btn", "type": "button", "label": "b"}]}]
                    },
                    "api_design": {"endpoints": [{"method": "GET", "path": "/test", "description": "test"}]},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0


_VALID_FULL_CONTENT = {
    "entity_definition": {"description": "d", "fields": []},
    "table_design": {"tables": []},
    "page_structure": {"pages": []},
    "api_design": {"endpoints": []},
    "constraints": {},
}


async def _spec_review(client, db, requirement, reviewer, action, comment=None):
    """置为 reviewing_spec、建 pending 规范审核、并以 reviewer 身份审批（approve/reject）。"""
    from app.models import RequirementReview

    requirement.status = "reviewing_spec"
    db.add(requirement)
    await db.flush()
    review = RequirementReview(
        requirement_id=requirement.id,
        review_type="specification",
        reviewer_id=reviewer.id,
        status="pending",
    )
    db.add(review)
    await db.commit()

    payload = {"action": action}
    if comment is not None:
        payload["comment"] = comment
    return await client.post(
        f"/api/v1/requirements/{requirement.id}/review",
        json=payload,
        headers=auth_headers(reviewer.id, permissions=["requirement:review_spec"]),
    )


class TestSpecDraftSetField:
    @pytest.mark.asyncio
    async def test_set_field_creates_draft_from_current_version(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "old", "fields": []})},
            headers=headers,
        )

        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "new desc"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["is_draft"] is True
        # 尚无审批版本，工作内容基于 base_version 0。
        assert body["data"]["base_version"] == 0

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["is_draft"] is True
        assert gdata["content"]["entity_definition"]["description"] == "new desc"
        assert gdata["content"]["table_design"] == {"tables": []}

    @pytest.mark.asyncio
    async def test_set_field_multiple_writes_accumulate(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "d1", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": [{"method": "GET", "path": "/a", "description": "a"}]},
                "constraints": {},
            }},
            headers=headers,
        )

        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "d2"},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "api_design.endpoints[0].description", "value": "updated"},
            headers=headers,
        )
        assert resp.json()["code"] == 0

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        content = get_resp.json()["data"]["content"]
        assert content["entity_definition"]["description"] == "d2"
        assert content["api_design"]["endpoints"][0]["description"] == "updated"

    @pytest.mark.asyncio
    async def test_set_field_status_not_drafting_spec(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "x"},
            headers=headers,
        )
        assert resp.json()["code"] == 40204

    @pytest.mark.asyncio
    async def test_set_field_path_not_found_actionable(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT)},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.nonexistent", "value": "x"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "description" in body["message"]

    @pytest.mark.asyncio
    async def test_set_field_schema_validation_fails_rolls_back(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT)},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.fields", "value": "not_an_array"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        assert get_resp.json()["code"] == 0


class TestSpecDraftCommitDiscard:
    @pytest.mark.asyncio
    async def test_commit_is_noop_no_version(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "v1", "fields": []})},
            headers=headers,
        )
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "v2-draft"},
            headers=headers,
        )

        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/specification/commit",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        # commit 不再生成版本（幂等 no-op）。
        assert body["data"].get("committed") is False

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["content"]["entity_definition"]["description"] == "v2-draft"
        assert gdata["current_version"] == 0

        versions = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )
        assert versions.json()["data"] == []

    @pytest.mark.asyncio
    async def test_commit_no_draft(
        self, client, normal_user, sample_requirement, db
    ):
        # 从未编辑过 → 无 spec 文档 → 无草稿可定版。
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/specification/commit",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "无草稿" in body["message"]

    @pytest.mark.asyncio
    async def test_discard_reverts_to_last_reviewed_version(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        # 编辑并经一次审核（驳回）→ 切出 v1 基线，状态回到 drafting_spec。
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "baseline", "fields": []})},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        await _spec_review(client, db, sample_requirement, another_user, "reject", comment="需修改")

        # 再次编辑草稿，然后丢弃 → 应回到已审版本 baseline。
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "edited"},
            headers=auth_headers(normal_user.id, permissions=["specification:edit"]),
        )
        resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft",
            headers=auth_headers(normal_user.id, permissions=["specification:edit"]),
        )
        assert resp.json()["code"] == 0

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["is_draft"] is False
        assert gdata["content"]["entity_definition"]["description"] == "baseline"


class TestSpecVersionOnReview:
    """版本只在规范审批（通过/驳回）时生成。"""

    @pytest.mark.asyncio
    async def test_spec_approve_creates_version(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "ready", "fields": []})},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        resp = await _spec_review(client, db, sample_requirement, another_user, "approve")
        assert resp.json()["code"] == 0

        versions = (await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )).json()["data"]
        assert len(versions) == 1
        assert versions[0]["version"] == 1
        assert versions[0]["content"]["entity_definition"]["description"] == "ready"

    @pytest.mark.asyncio
    async def test_spec_reject_creates_version(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "rough", "fields": []})},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        resp = await _spec_review(client, db, sample_requirement, another_user, "reject", comment="需完善")
        assert resp.json()["code"] == 0

        versions = (await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )).json()["data"]
        assert len(versions) == 1
        assert versions[0]["content"]["entity_definition"]["description"] == "rough"

    @pytest.mark.asyncio
    async def test_multiple_edits_before_review_single_version(
        self, client, normal_user, another_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        edit_headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])

        # 多次全量保存 + 字段级编辑，均不产生版本。
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "d1", "fields": []})},
            headers=edit_headers,
        )
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": dict(_VALID_FULL_CONTENT, entity_definition={"description": "d2", "fields": []})},
            headers=edit_headers,
        )
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "d3"},
            headers=edit_headers,
        )

        pre = (await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )).json()["data"]
        assert pre == []

        # 审批一次 → 只切出一个版本，内容为最终的 d3。
        await _spec_review(client, db, sample_requirement, another_user, "approve")
        post = (await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification/versions",
            headers=auth_headers(normal_user.id),
        )).json()["data"]
        assert len(post) == 1
        assert post[0]["content"]["entity_definition"]["description"] == "d3"
