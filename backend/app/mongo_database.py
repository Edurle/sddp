from motor.motor_asyncio import AsyncIOMotorClient

from app.config import MONGO_URL

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


def get_database():
    return get_mongo_client().sdd


def get_spec_templates_collection():
    return get_database().specification_templates


def get_spec_documents_collection():
    return get_database().specification_documents


async def ensure_indexes():
    templates = get_spec_templates_collection()
    await templates.create_index("team_id", unique=True)
    documents = get_spec_documents_collection()
    await documents.create_index("requirement_id", unique=True)
