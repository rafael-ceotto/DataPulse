"""create hospital_enrollments table

Revision ID: 368a6ece2e6d
Revises: be283768582e
Create Date: 2026-10-12 10:05:57.115273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '368a6ece2e6d'
down_revision: Union[str, Sequence[str], None] = 'be283768582e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('hospital_enrollments',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('facility_id', sa.String(), nullable=False),
    sa.Column('npi', sa.String(), nullable=True),
    sa.Column('organization_name', sa.String(), nullable=True),
    sa.Column('enrollment_state', sa.String(), nullable=True),
    sa.Column('proprietary_nonprofit', sa.String(), nullable=True),
    sa.Column('is_acute_care', sa.Boolean(), nullable=False),
    sa.Column('is_psychiatric', sa.Boolean(), nullable=False),
    sa.Column('is_rehabilitation', sa.Boolean(), nullable=False),
    sa.Column('is_childrens', sa.Boolean(), nullable=False),
    sa.Column('is_long_term', sa.Boolean(), nullable=False),
    sa.Column('is_swing_bed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['facility_id'], ['hospitals.facility_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('facility_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('hospital_enrollments')