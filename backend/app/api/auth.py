from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db_session
from app.services import auth as auth_service

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db_session)) -> dict:
    result = await auth_service.login(db, body.email, body.password, body.remember)
    return {"code": 0, "message": "success", "data": result}
