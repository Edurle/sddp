import pytest
from tests.conftest import auth_headers


class TestDefaultTemplateAgentPrompt:
    @pytest.mark.asyncio
    async def test_default_template_has_agent_prompt_on_all_fields(self):
        from app.mongo_models.spec_template import SpecTemplate

        template = SpecTemplate()
        sections = template.DEFAULT_SECTIONS

        expected_prompts = {
            ("entity_definition", "description"): "用一段话描述该实体的用途和核心职责",
            ("entity_definition", "fields"): "列出实体的所有字段。每个字段需包含 name（字段名，英文小写下划线）、type（数据类型，如 string/integer/boolean/datetime/json）、constraints（约束数组，如 ['required', 'unique', 'max:255'])",
            ("table_design", "tables"): "列出所有数据库表。每张表需包含 name（表名，复数形式）、description（表用途）、fields（字段数组，包含 name/type/nullable/default/comment/primary_key/unique/foreign_key/auto_increment）、indexes（索引数组）",
            ("page_structure", "pages"): "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/interaction）",
            ("api_design", "endpoints"): "列出所有 API 接口。每个接口需包含 method（GET/POST/PUT/DELETE/PATCH）、path（URL路径）、description（接口说明）、request_params（请求参数数组，含 name/in/type/required/description）、response（响应体结构，含 code/message/data）、errors（错误码数组）",
            ("constraints", "directory_structure"): "描述项目的目录结构规范",
            ("constraints", "naming_conventions"): "描述编码命名规范（变量、函数、文件等）",
            ("constraints", "other"): "描述其他技术约束（性能要求、安全要求等）",
        }

        for section in sections:
            for field_def in section.get("fields", []):
                key = (section["name"], field_def["name"])
                assert key in expected_prompts, f"Missing expected prompt for {key}"
                assert field_def.get("agent_prompt") is not None, f"agent_prompt missing for {key}"
                assert field_def["agent_prompt"] == expected_prompts[key], (
                    f"agent_prompt mismatch for {key}: got '{field_def.get('agent_prompt')}'"
                )


class TestAgentPromptSerialization:
    @pytest.mark.asyncio
    async def test_custom_template_agent_prompt_preserved_through_save_read(
        self, client, normal_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["spec_template:edit"])

        custom_sections = [
            {
                "name": "custom_section",
                "display_name": "自定义章节",
                "required": True,
                "fields": [
                    {
                        "name": "custom_field",
                        "display_name": "自定义字段",
                        "type": "text",
                        "required": True,
                        "description": "A custom field",
                        "agent_prompt": "请描述自定义内容",
                    }
                ],
            }
        ]

        resp = await client.put(
            f"/api/v1/teams/{team.id}/spec-template",
            json={"sections": custom_sections},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

        field_data = body["data"]["sections"][0]["fields"][0]
        assert field_data["agent_prompt"] == "请描述自定义内容"

        headers_get = auth_headers(normal_user.id)
        resp2 = await client.get(
            f"/api/v1/teams/{team.id}/spec-template",
            headers=headers_get,
        )
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert body2["code"] == 0
        field_data2 = body2["data"]["sections"][0]["fields"][0]
        assert field_data2["agent_prompt"] == "请描述自定义内容"

    @pytest.mark.asyncio
    async def test_to_document_includes_agent_prompt(self):
        from app.mongo_models.spec_template import SpecTemplate, SpecTemplateField, SpecTemplateSection

        template = SpecTemplate(team_id=1)
        template.sections = [
            SpecTemplateSection(
                name="test_section",
                display_name="Test Section",
                fields=[
                    SpecTemplateField(
                        name="f1",
                        display_name="Field 1",
                        type="text",
                        agent_prompt="prompt for f1",
                    ),
                    SpecTemplateField(
                        name="f2",
                        display_name="Field 2",
                        type="text",
                    ),
                ],
            )
        ]

        doc = template.to_document()
        fields = doc["sections"][0]["fields"]
        assert fields[0]["agent_prompt"] == "prompt for f1"
        assert fields[1]["agent_prompt"] is None


class TestAgentGuideEndpoint:
    @pytest.mark.asyncio
    async def test_agent_guide_returns_agent_prompt_for_each_field(
        self, client, normal_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)

        resp = await client.get(
            f"/api/v1/teams/{team.id}/spec-template/agent-guide",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

        sections = body["data"]["sections"]
        assert len(sections) > 0

        all_prompts = []
        for section in sections:
            for field_def in section.get("fields", []):
                all_prompts.append((section["name"], field_def["name"], field_def.get("agent_prompt")))

        assert len(all_prompts) >= 8
        for section_name, field_name, prompt in all_prompts:
            assert prompt is not None, f"agent_prompt is None for {section_name}.{field_name}"

    @pytest.mark.asyncio
    async def test_agent_guide_non_member_forbidden(
        self, client, another_user, owner_role
    ):
        team = owner_role["team"]
        headers = auth_headers(another_user.id)

        resp = await client.get(
            f"/api/v1/teams/{team.id}/spec-template/agent-guide",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40300
