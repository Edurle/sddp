from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class VerifyEmailRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register")
async def register(body: RegisterRequest) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/login")
async def login(body: LoginRequest) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest) -> dict:
    raise NotImplementedError("Not implemented yet")
