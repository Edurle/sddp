from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ApiResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    nickname: str = Field(min_length=2, max_length=32)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


class UserInfoBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    avatar: str | None = None
    is_admin: bool = False


class LoginResponse(BaseModel):
    token: str
    user: UserInfoBrief


class LoginResponseWrapper(ApiResponse[LoginResponse]):
    pass


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=64)
