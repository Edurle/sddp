from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReviewComment


async def create_review_comment(
    db: AsyncSession,
    requirement_id: int,
    reviewer_id: int,
    review_type: str,
    action: str,
    comment: str | None = None,
) -> dict:
    rc = ReviewComment(
        requirement_id=requirement_id,
        reviewer_id=reviewer_id,
        review_type=review_type,
        action=action,
        comment=comment,
    )
    db.add(rc)
    await db.flush()
    await db.refresh(rc)
    return _to_dict(rc)


async def list_review_comments(
    db: AsyncSession,
    requirement_id: int,
) -> list[dict]:
    stmt = (
        select(ReviewComment)
        .where(ReviewComment.requirement_id == requirement_id)
        .order_by(ReviewComment.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_to_dict(r) for r in rows]


def _to_dict(rc: ReviewComment) -> dict:
    return {
        "id": rc.id,
        "requirement_id": rc.requirement_id,
        "reviewer_id": rc.reviewer_id,
        "review_type": rc.review_type,
        "action": rc.action,
        "comment": rc.comment,
        "created_at": rc.created_at.isoformat() if rc.created_at else None,
    }
