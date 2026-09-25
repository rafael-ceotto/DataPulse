"""add multi-country support to hospitals

Revision ID: be283768582e
Revises: b13f8d430add
Create Date: 2026-09-24 13:49:14.665853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'be283768582e'
down_revision: Union[str, Sequence[str], None] = 'b13f8d430add'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('country', sa.String(2), nullable=True, server_default='US'))
    op.add_column('hospitals', sa.Column('normalized_score', sa.Float(), nullable=True))
    op.add_column('hospitals', sa.Column('rating_system', sa.String(50), nullable=True))
    op.add_column('hospitals', sa.Column('raw_rating_label', sa.String(100), nullable=True))
    op.create_index('idx_hospitals_country', 'hospitals', ['country'])


def downgrade() -> None:
    op.drop_index('idx_hospitals_country', table_name='hospitals')
    op.drop_column('hospitals', 'raw_rating_label')
    op.drop_column('hospitals', 'rating_system')
    op.drop_column('hospitals', 'normalized_score')
    op.drop_column('hospitals', 'country')