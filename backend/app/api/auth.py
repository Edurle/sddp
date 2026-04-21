from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.services import auth as auth_service

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    nickname: str = Field(min_length=2, max_length=32)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=64)


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.register(db, body.email, body.password, body.nickname)
    return {"code": 0, "message": result["message"], "data": result.get("user")}


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.verify_email(db, body.token)
    return {"code": 0, "message": result["message"], "data": None}


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.login(db, body.email, body.password, body.remember)
    return {"code": 0, "message": "success", "data": result}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.forgot_password(db, body.email)
    return {"code": 0, "message": result["message"], "data": None}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.reset_password(db, body.token, body.new_password)
    return {"code": 0, "message": result["message"], "data": None}
