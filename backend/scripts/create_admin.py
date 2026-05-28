import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import init_db, async_session
from app.models.user import User
from app.utils.security import hash_password
from sqlalchemy import select


async def create_admin():
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "")
    nickname = os.getenv("ADMIN_NICKNAME", "管理员")

    if not password:
        print("ERROR: ADMIN_PASSWORD env var is required")
        sys.exit(1)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"Admin user already exists: {email}")
            return

        admin = User(
            email=email,
            nickname=nickname,
            password_hash=hash_password(password),
            email_verified=True,
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user created: {email}")


async def main():
    await init_db()
    await create_admin()


if __name__ == "__main__":
    asyncio.run(main())
