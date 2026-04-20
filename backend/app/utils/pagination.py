from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    query: Select,
    page: int,
    page_size: int,
    db: AsyncSession,
) -> dict[str, Any]:
    page = max(page, 1)
    page_size = max(1, min(page_size, 100))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    items_query = query.offset(offset).limit(page_size)
    result = await db.execute(items_query)
    rows = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": rows,
    }
