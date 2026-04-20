from datetime import datetime, timedelta, timezone

from app.models import PasswordResetToken, User
from app.utils.security import hash_password
from tests.conftest import auth_headers


# ============================================================
# 1.1 Register (POST /api/v1/auth/register) - TC-AUTH-001~012
# ============================================================


async def test_register_success(client, db):
    data = {"email": "new@example.com", "password": "12345678", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "注册成功" in body["message"]


async def test_register_missing_email(client, db):
    data = {"password": "12345678", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_missing_password(client, db):
    data = {"email": "new@example.com", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_missing_nickname(client, db):
    data = {"email": "new@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_invalid_email_format(client, db):
    data = {"email": "invalid-email", "password": "12345678", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_empty_email(client, db):
    data = {"email": "", "password": "12345678", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_password_too_short(client, db):
    data = {"email": "new@example.com", "password": "1234567", "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_password_too_long(client, db):
    data = {"email": "new@example.com", "password": "a" * 65, "nickname": "新用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_nickname_too_short(client, db):
    data = {"email": "new@example.com", "password": "12345678", "nickname": "A"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_nickname_too_long(client, db):
    data = {"email": "new@example.com", "password": "12345678", "nickname": "A" * 33}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_register_email_already_exists(client, normal_user, db):
    data = {"email": normal_user.email, "password": "12345678", "nickname": "用户"}
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40002


async def test_register_empty_body(client, db):
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 200
    assert response.json()["code"] == 40001


# ============================================================
# 1.2 Verify Email (POST /api/v1/auth/verify-email) - TC-AUTH-013~018
# ============================================================


async def _create_unverified_user(db, email="verify@example.com", nickname="验证用户"):
    user = User(
        email=email,
        nickname=nickname,
        password_hash=hash_password("12345678"),
        is_active=True,
        is_admin=False,
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_token(db, user_id, token, expires_at, used=False):
    record = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        used=used,
    )
    db.add(record)
    await db.commit()


async def test_verify_email_success(client, db):
    user = await _create_unverified_user(db, "verify-ok@example.com")
    await _create_token(
        db, user.id, "valid-verify-token",
        datetime.now(timezone.utc) + timedelta(hours=24),
    )
    response = await client.post("/api/v1/auth/verify-email", json={"token": "valid-verify-token"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "邮箱验证成功" in body["message"]


async def test_verify_email_empty_token(client, db):
    response = await client.post("/api/v1/auth/verify-email", json={"token": ""})
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_verify_email_invalid_token(client, db):
    response = await client.post("/api/v1/auth/verify-email", json={"token": "invalid-random-token"})
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_verify_email_expired_token(client, db):
    user = await _create_unverified_user(db, "expired-verify@example.com", "过期验证")
    await _create_token(
        db, user.id, "expired-verify-token",
        datetime.now(timezone.utc) - timedelta(hours=1),
    )
    response = await client.post("/api/v1/auth/verify-email", json={"token": "expired-verify-token"})
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_verify_email_used_token(client, db):
    user = await _create_unverified_user(db, "used-verify@example.com", "已用验证")
    await _create_token(
        db, user.id, "used-verify-token",
        datetime.now(timezone.utc) + timedelta(hours=24),
        used=True,
    )
    response = await client.post("/api/v1/auth/verify-email", json={"token": "used-verify-token"})
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_verify_email_missing_token(client, db):
    response = await client.post("/api/v1/auth/verify-email", json={})
    assert response.status_code == 200
    assert response.json()["code"] == 40001


# ============================================================
# 1.3 Login (POST /api/v1/auth/login) - TC-AUTH-019~028
# ============================================================


async def test_login_success(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "token" in body["data"]
    assert "user" in body["data"]
    assert body["data"]["user"]["email"] == "user@example.com"


async def test_login_wrong_password(client, normal_user, db):
    data = {"email": "user@example.com", "password": "wrongpass1"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40003


async def test_login_user_not_found(client, db):
    data = {"email": "nobody@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40003


async def test_login_email_unverified(client, unverified_user, db):
    data = {"email": "unverified@example.com", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40004


async def test_login_remember_true(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678", "remember": True}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 0


async def test_login_remember_false(client, normal_user, db):
    data = {"email": "user@example.com", "password": "12345678", "remember": False}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 0


async def test_login_missing_email(client, db):
    data = {"password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_missing_password(client, db):
    data = {"email": "user@example.com"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_invalid_email_format(client, db):
    data = {"email": "not-an-email", "password": "12345678"}
    response = await client.post("/api/v1/auth/login", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_login_empty_body(client, db):
    response = await client.post("/api/v1/auth/login", json={})
    assert response.status_code == 200
    assert response.json()["code"] == 40001


# ============================================================
# 1.4 Forgot Password (POST /api/v1/auth/forgot-password) - TC-AUTH-029~032
# ============================================================


async def test_forgot_password_success(client, normal_user, db):
    data = {"email": "user@example.com"}
    response = await client.post("/api/v1/auth/forgot-password", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "重置邮件已发送" in body["message"]


async def test_forgot_password_nonexistent_email(client, db):
    data = {"email": "nobody@example.com"}
    response = await client.post("/api/v1/auth/forgot-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 0


async def test_forgot_password_invalid_email(client, db):
    data = {"email": "invalid-email"}
    response = await client.post("/api/v1/auth/forgot-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_forgot_password_missing_email(client, db):
    response = await client.post("/api/v1/auth/forgot-password", json={})
    assert response.status_code == 200
    assert response.json()["code"] == 40001


# ============================================================
# 1.5 Reset Password (POST /api/v1/auth/reset-password) - TC-AUTH-033~040
# ============================================================


async def _create_reset_token(db, user_id, token, hours=1, used=False):
    record = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
        used=used,
    )
    db.add(record)
    await db.commit()


async def test_reset_password_success(client, normal_user, db):
    await _create_reset_token(db, normal_user.id, "valid-reset-token")
    data = {"token": "valid-reset-token", "new_password": "newpass123"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert "密码重置成功" in body["message"]


async def test_reset_password_invalid_token(client, db):
    data = {"token": "invalid-token", "new_password": "newpass123"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_reset_password_expired_token(client, normal_user, db):
    record = PasswordResetToken(
        user_id=normal_user.id,
        token="expired-reset-token",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        used=False,
    )
    db.add(record)
    await db.commit()

    data = {"token": "expired-reset-token", "new_password": "newpass123"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40400


async def test_reset_password_new_password_too_short(client, normal_user, db):
    await _create_reset_token(db, normal_user.id, "valid-reset-token")
    data = {"token": "valid-reset-token", "new_password": "1234567"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_reset_password_new_password_too_long(client, normal_user, db):
    await _create_reset_token(db, normal_user.id, "valid-reset-token")
    data = {"token": "valid-reset-token", "new_password": "a" * 65}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_reset_password_empty_token(client, db):
    data = {"token": "", "new_password": "newpass123"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_reset_password_missing_token(client, db):
    data = {"new_password": "newpass123"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001


async def test_reset_password_missing_new_password(client, db):
    data = {"token": "valid-reset-token"}
    response = await client.post("/api/v1/auth/reset-password", json=data)
    assert response.status_code == 200
    assert response.json()["code"] == 40001
