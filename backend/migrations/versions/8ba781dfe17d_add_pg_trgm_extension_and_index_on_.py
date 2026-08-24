"""add pg_trgm extension and index on facility_name

Revision ID: 8ba781dfe17d
Revises: 8579784dae8b
Create Date: 2026-08-24 13:53:10.126329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ba781dfe17d'
down_revision: Union[str, Sequence[str], None] = '8579784dae8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX IF NOT EXISTS hospitals_name_trgm ON hospitals USING GIN (facility_name gin_trgm_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS hospitals_name_trgm")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
