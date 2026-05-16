"""add review_comments table

Revision ID: 3907015ac419
Revises: a3a8bc997520
Create Date: 2026-05-16 22:44:23.811182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3907015ac419'
down_revision: Union[str, Sequence[str], None] = 'a3a8bc997520'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_comments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requirement_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=False),
        sa.Column("review_type", sa.String(20), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rc_requirement", "review_comments", ["requirement_id"])
    op.create_index("idx_rc_reviewer", "review_comments", ["reviewer_id"])


def downgrade() -> None:
    op.drop_index("idx_rc_reviewer", table_name="review_comments")
    op.drop_index("idx_rc_requirement", table_name="review_comments")
    op.drop_table("review_comments")
