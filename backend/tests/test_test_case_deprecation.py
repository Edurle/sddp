import pytest
from sqlalchemy import select

from tests.conftest import auth_headers


async def _add_tc(db, req_id, seq=1, status="active", case_type="happy_path"):
    from app.models import TestCase

    tc = TestCase(
        requirement_id=req_id,
        case_number=f"TC-{req_id}-{seq:03d}",
        title=f"用例{seq}",
        case_type=case_type,
        steps="步骤",
        expected_result="预期",
        status=status,
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc


async def _tc_status(db, tc_id):
    from app.models import TestCase

    return (await db.execute(select(TestCase.status).where(TestCase.id == tc_id))).scalar_one()


class TestAutoDeprecateOnRequirementDeprecation:
    @pytest.mark.asyncio
    async def test_direct_deprecate_requirement_deprecates_cases(
        self, client, normal_user, approved_requirement, db
    ):
        tc1 = await _add_tc(db, approved_requirement.id, 1)
        tc2 = await _add_tc(db, approved_requirement.id, 2)

        resp = await client.patch(
            f"/api/v1/requirements/{approved_requirement.id}",
            json={"status": "deprecated"},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        assert resp.json()["code"] == 0
        assert await _tc_status(db, tc1.id) == "deprecated"
        assert await _tc_status(db, tc2.id) == "deprecated"

    @pytest.mark.asyncio
    async def test_supersede_from_approved_deprecates_cases(
        self, client, normal_user, approved_requirement, db
    ):
        tc = await _add_tc(db, approved_requirement.id, 1)
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/supersede",
            json={},
            headers=auth_headers(normal_user.id, permissions=["requirement:create"]),
        )
        assert resp.json()["code"] == 0
        assert await _tc_status(db, tc.id) == "deprecated"

    @pytest.mark.asyncio
    async def test_supersede_from_drafting_tests_keeps_cases(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_tests"
        db.add(sample_requirement)
        await db.commit()
        tc = await _add_tc(db, sample_requirement.id, 1)

        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/supersede",
            json={},
            headers=auth_headers(normal_user.id, permissions=["requirement:create"]),
        )
        assert resp.json()["code"] == 0
        # 未过审 → 用例原样保留
        assert await _tc_status(db, tc.id) == "active"

    @pytest.mark.asyncio
    async def test_relates_to_does_not_deprecate(
        self, client, normal_user, approved_requirement, sample_requirement, db
    ):
        tc = await _add_tc(db, approved_requirement.id, 1)
        resp = await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/links",
            json={"target_id": sample_requirement.id, "link_type": "relates_to"},
            headers=auth_headers(normal_user.id, permissions=["requirement:edit"]),
        )
        assert resp.json()["code"] == 0
        assert await _tc_status(db, tc.id) == "active"


class TestManualDeprecate:
    @pytest.mark.asyncio
    async def test_manual_deprecate_approved_ok(
        self, client, normal_user, approved_requirement, db
    ):
        tc = await _add_tc(db, approved_requirement.id, 1)
        resp = await client.post(
            f"/api/v1/test-cases/{tc.id}/deprecate",
            headers=auth_headers(normal_user.id, permissions=["test_case:edit"]),
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "deprecated"

    @pytest.mark.asyncio
    async def test_manual_deprecate_requires_approved(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_tests"
        db.add(sample_requirement)
        await db.commit()
        tc = await _add_tc(db, sample_requirement.id, 1)

        resp = await client.post(
            f"/api/v1/test-cases/{tc.id}/deprecate",
            headers=auth_headers(normal_user.id, permissions=["test_case:edit"]),
        )
        assert resp.json()["code"] == 40204  # ERR_REQUIREMENT_STATUS

    @pytest.mark.asyncio
    async def test_manual_deprecate_already_deprecated(
        self, client, normal_user, approved_requirement, db
    ):
        tc = await _add_tc(db, approved_requirement.id, 1, status="deprecated")
        resp = await client.post(
            f"/api/v1/test-cases/{tc.id}/deprecate",
            headers=auth_headers(normal_user.id, permissions=["test_case:edit"]),
        )
        assert resp.json()["code"] == 40204


class TestListAndCoverageExcludeDeprecated:
    @pytest.mark.asyncio
    async def test_list_excludes_deprecated_by_default(
        self, client, normal_user, approved_requirement, db
    ):
        await _add_tc(db, approved_requirement.id, 1, status="active")
        await _add_tc(db, approved_requirement.id, 2, status="deprecated")
        headers = auth_headers(normal_user.id)

        resp = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/test-cases", headers=headers
        )
        items = resp.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["status"] == "active"

        resp2 = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/test-cases?include_deprecated=true",
            headers=headers,
        )
        assert len(resp2.json()["data"]["items"]) == 2

    @pytest.mark.asyncio
    async def test_coverage_excludes_deprecated(
        self, client, normal_user, approved_requirement, db
    ):
        await _add_tc(db, approved_requirement.id, 1, status="active")
        await _add_tc(db, approved_requirement.id, 2, status="deprecated")

        resp = await client.get(
            f"/api/v1/requirements/{approved_requirement.id}/test-statistics",
            headers=auth_headers(normal_user.id),
        )
        assert resp.json()["data"]["total_cases"] == 1
