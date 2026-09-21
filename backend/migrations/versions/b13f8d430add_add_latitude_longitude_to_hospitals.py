"""add latitude longitude to hospitals

Revision ID: b13f8d430add
Revises: e8ffb590bb5c
Create Date: 2026-09-21 10:50:03.654592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b13f8d430add'
down_revision: Union[str, Sequence[str], None] = 'e8ffb590bb5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('hospitals', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('hospitals', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('hospitals', 'longitude')
    op.drop_column('hospitals', 'latitude')