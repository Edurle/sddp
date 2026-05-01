import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_mongo():
    templates_col = AsyncMock()
    templates_col.find_one = AsyncMock(return_value=None)
    templates_col.update_one = AsyncMock()

    documents_col = AsyncMock()
    documents_col.find_one = AsyncMock(return_value=None)
    documents_col.update_one = AsyncMock()

    with patch(
        "app.services.specification.get_spec_templates_collection",
        return_value=templates_col,
    ), patch(
        "app.services.specification.get_spec_documents_collection",
        return_value=documents_col,
    ):
        yield {"templates": templates_col, "documents": documents_col}


class TestTemplateMongoPersistence:
    @pytest.mark.asyncio
    async def test_save_then_read_back(self, db, normal_user, owner_role, mock_mongo):
        templates_col = mock_mongo["templates"]
        team = owner_role["team"]

        from app.services.specification import update_spec_template

        sections = [
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
                    }
                ],
            }
        ]

        result = await update_spec_template(db, team.id, normal_user.id, sections)
        assert "sections" in result
        assert result["sections"][0]["name"] == "custom_section"

        templates_col.update_one.assert_called_once()
        call_args = templates_col.update_one.call_args
        assert call_args[0][0] == {"team_id": team.id}
        update_doc = call_args[0][1]["$set"]
        assert update_doc["team_id"] == team.id
        assert update_doc["sections"][0]["name"] == "custom_section"
        assert call_args[1]["upsert"] is True

        templates_col.find_one.return_value = update_doc

        from app.services.specification import get_spec_template

        result2 = await get_spec_template(db, team.id, normal_user.id)
        assert result2["sections"][0]["name"] == "custom_section"

    @pytest.mark.asyncio
    async def test_returns_default_when_not_in_mongo(
        self, db, normal_user, owner_role, mock_mongo
    ):
        team = owner_role["team"]

        from app.services.specification import get_spec_template

        result = await get_spec_template(db, team.id, normal_user.id)
        assert "sections" in result
        assert len(result["sections"]) > 0
        assert result["sections"][0]["name"] == "entity_definition"


class TestDocumentMongoPersistence:
    @pytest.mark.asyncio
    async def test_save_creates_first_version(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        documents_col = mock_mongo["documents"]
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        from app.services.specification import save_spec_document

        content = _valid_content()
        result = await save_spec_document(
            db, sample_requirement.id, normal_user.id, content
        )
        assert result["version"] == 1

        documents_col.update_one.assert_called_once()
        update_data = documents_col.update_one.call_args[0][1]["$set"]
        assert update_data["current_version"] == 1
        assert len(update_data["versions"]) == 1

    @pytest.mark.asyncio
    async def test_read_back_saved_document(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        documents_col = mock_mongo["documents"]
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        from app.services.specification import save_spec_document, get_spec_document

        content = _valid_content()
        await save_spec_document(db, sample_requirement.id, normal_user.id, content)

        saved = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved

        result = await get_spec_document(db, sample_requirement.id)
        assert result["current_version"] == 1
        assert result["content"] is not None

    @pytest.mark.asyncio
    async def test_version_increments_on_second_save(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        documents_col = mock_mongo["documents"]
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        from app.services.specification import save_spec_document

        content_v1 = _valid_content(description="v1")
        result1 = await save_spec_document(
            db, sample_requirement.id, normal_user.id, content_v1
        )
        assert result1["version"] == 1

        saved_v1 = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved_v1

        content_v2 = _valid_content(description="v2")
        result2 = await save_spec_document(
            db, sample_requirement.id, normal_user.id, content_v2
        )
        assert result2["version"] == 2

        saved_v2 = documents_col.update_one.call_args[0][1]["$set"]
        assert saved_v2["current_version"] == 2
        assert len(saved_v2["versions"]) == 2


class TestVersionHistoryPreservation:
    @pytest.mark.asyncio
    async def test_list_versions_returns_all(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        documents_col = mock_mongo["documents"]
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        from app.services.specification import save_spec_document, list_spec_versions

        await save_spec_document(
            db, sample_requirement.id, normal_user.id, _valid_content(description="v1")
        )
        saved_v1 = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved_v1

        await save_spec_document(
            db, sample_requirement.id, normal_user.id, _valid_content(description="v2")
        )
        saved_v2 = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved_v2

        versions = await list_spec_versions(db, sample_requirement.id)
        assert len(versions) == 2
        assert versions[0]["version"] == 1
        assert versions[1]["version"] == 2

    @pytest.mark.asyncio
    async def test_version_detail_preserves_old_content(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        documents_col = mock_mongo["documents"]
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        from app.services.specification import (
            save_spec_document,
            get_spec_version_detail,
        )

        await save_spec_document(
            db, sample_requirement.id, normal_user.id, _valid_content(description="v1")
        )
        saved_v1 = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved_v1

        await save_spec_document(
            db, sample_requirement.id, normal_user.id, _valid_content(description="v2")
        )
        saved_v2 = documents_col.update_one.call_args[0][1]["$set"]
        documents_col.find_one.return_value = saved_v2

        detail_v1 = await get_spec_version_detail(db, sample_requirement.id, 1)
        assert detail_v1["version"] == 1
        assert detail_v1["content"]["entity_definition"]["description"] == "v1"

        detail_v2 = await get_spec_version_detail(db, sample_requirement.id, 2)
        assert detail_v2["version"] == 2
        assert detail_v2["content"]["entity_definition"]["description"] == "v2"

    @pytest.mark.asyncio
    async def test_empty_versions_when_no_saves(
        self, db, normal_user, owner_role, sample_requirement, mock_mongo
    ):
        from app.services.specification import list_spec_versions

        versions = await list_spec_versions(db, sample_requirement.id)
        assert versions == []


def _valid_content(description="test"):
    return {
        "entity_definition": {
            "description": description,
            "fields": [{"name": "id", "type": "INT"}],
        },
        "table_design": {"tables": [{"name": "t", "fields": [{"name": "id", "type": "INT"}]}]},
        "page_structure": {
            "pages": [
                {"name": "p", "code": "p", "elements": [{"code": "b", "type": "button", "label": "b"}]}
            ]
        },
        "api_design": {"endpoints": [{"method": "GET", "path": "/t", "description": "test"}]},
        "constraints": {},
    }
