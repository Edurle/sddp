import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sdd.db")
REDIS_URL = os.getenv("REDIS_URL", "")

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
REMEMBER_TOKEN_EXPIRE_DAYS = int(os.getenv("REMEMBER_TOKEN_EXPIRE_DAYS", "30"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
