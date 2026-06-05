"""add requirement_links table

Revision ID: a1b2c3d4e5f6
Revises: 4a7b2c8d9e01
Create Date: 2026-06-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4a7b2c8d9e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'requirement_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.String(length=20), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['requirements.id']),
        sa.ForeignKeyConstraint(['target_id'], ['requirements.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('source_id', 'target_id', 'link_type', name='uq_req_link'),
    )
    op.create_index('idx_link_source', 'requirement_links', ['source_id'])
    op.create_index('idx_link_target', 'requirement_links', ['target_id'])


def downgrade() -> None:
    op.drop_index('idx_link_target', table_name='requirement_links')
    op.drop_index('idx_link_source', table_name='requirement_links')
    op.drop_table('requirement_links')
