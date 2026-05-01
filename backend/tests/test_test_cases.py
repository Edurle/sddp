import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_test_cases_success(client, db, sample_test_case, normal_user):
    headers = auth_headers(normal_user.id)
    req_id = sample_test_case.requirement_id
    resp = await client.get(f"/api/v1/requirements/{req_id}/test-cases", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], dict)
    assert "items" in body["data"]
    assert len(body["data"]["items"]) >= 1
    tc = body["data"]["items"][0]
    assert "id" in tc
    assert "case_number" in tc
    assert "title" in tc
    assert "case_type" in tc
    assert "steps" in tc
    assert "expected_result" in tc


@pytest.mark.asyncio
async def test_list_test_cases_filter_by_type(client, db, sample_test_case, normal_user):
    headers = auth_headers(normal_user.id)
    req_id = sample_test_case.requirement_id
    resp = await client.get(
        f"/api/v1/requirements/{req_id}/test-cases",
        params={"case_type": "api"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    for tc in body["data"]["items"]:
        assert tc["case_type"] == "api"


@pytest.mark.asyncio
async def test_list_test_cases_excludes_soft_deleted(client, db, sample_test_case, normal_user):
    from app.models import TestCase

    sample_test_case.is_deleted = True
    await db.commit()

    headers = auth_headers(normal_user.id)
    req_id = sample_test_case.requirement_id
    resp = await client.get(f"/api/v1/requirements/{req_id}/test-cases", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    for tc in body["data"]["items"]:
        assert tc["id"] != sample_test_case.id


@pytest.mark.asyncio
async def test_create_test_case_success(client, db, approved_requirement, normal_user, owner_role):
    from app.models import Requirement

    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "登录成功",
            "case_type": "api",
            "precondition": "用户已注册",
            "steps": "发送登录请求",
            "expected_result": "返回token",
            "related_api": "/api/v1/auth/login",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert "id" in body["data"]
    assert "case_number" in body["data"]


@pytest.mark.asyncio
async def test_create_test_case_auto_case_number(client, db, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "登录失败",
            "case_type": "api",
            "precondition": "用户未注册",
            "steps": "发送错误密码",
            "expected_result": "返回401",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    case_number = body["data"]["case_number"]
    assert case_number.startswith(f"TC-{approved_requirement.id}-")


@pytest.mark.asyncio
async def test_create_test_case_e2e_with_related_element(client, db, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "E2E登录流程",
            "case_type": "e2e",
            "precondition": "用户在登录页",
            "steps": "点击登录按钮",
            "expected_result": "跳转首页",
            "related_element": "login-btn-submit",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_create_test_case_reviewing_status_forbidden(client, db, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "reviewing_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "测试",
            "case_type": "api",
            "precondition": "无",
            "steps": "步骤",
            "expected_result": "结果",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_create_test_case_approved_status_forbidden(client, db, approved_requirement, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "测试",
            "case_type": "api",
            "precondition": "无",
            "steps": "步骤",
            "expected_result": "结果",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_create_test_case_empty_title(client, db, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={"title": ""},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40001


@pytest.mark.asyncio
async def test_create_test_case_empty_steps(client, db, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        json={
            "title": "有标题",
            "case_type": "api",
            "steps": "",
            "expected_result": "结果",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40001


@pytest.mark.asyncio
async def test_update_test_case_success(client, db, sample_test_case, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-cases/{sample_test_case.id}",
        json={"title": "更新标题", "steps": "新步骤"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_test_case_reviewing_forbidden(client, db, sample_test_case, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "reviewing_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-cases/{sample_test_case.id}",
        json={"title": "不应成功"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_delete_test_case_success(client, db, sample_test_case, approved_requirement, normal_user, owner_role):
    approved_requirement.status = "drafting_tests"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/test-cases/{sample_test_case.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_delete_test_case_approved_forbidden(client, db, sample_test_case, approved_requirement, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/test-cases/{sample_test_case.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204
