"""add submit_review permissions

Revision ID: f1a2b3c4d5e6
Revises: e9b5f5b096be
Create Date: 2026-06-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = ('e9b5f5b096be', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_PERMISSIONS = [
    "requirement:submit_review_req",
    "requirement:submit_review_spec",
    "requirement:submit_review_tests",
]


def upgrade() -> None:
    rp = sa.table('role_permissions', sa.column('role_id', sa.Integer), sa.column('permission', sa.String))
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT DISTINCT role_id FROM role_permissions WHERE permission = :perm"),
        {"perm": "requirement:edit"},
    )
    role_ids = [row[0] for row in result.fetchall()]
    for role_id in role_ids:
        for perm in NEW_PERMISSIONS:
            existing = conn.execute(
                sa.text("SELECT 1 FROM role_permissions WHERE role_id = :rid AND permission = :perm"),
                {"rid": role_id, "perm": perm},
            ).fetchone()
            if not existing:
                conn.execute(rp.insert().values(role_id=role_id, permission=perm))


def downgrade() -> None:
    for perm in NEW_PERMISSIONS:
        op.execute(
            sa.text("DELETE FROM role_permissions WHERE permission = :perm").bindparams(perm=perm)
        )
