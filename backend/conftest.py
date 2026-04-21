import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def _clear_cache():
    from app.cache import cache_instance
    cache_instance._store.clear()
    cache_instance._expiry.clear()
    yield
    cache_instance._store.clear()
    cache_instance._expiry.clear()
