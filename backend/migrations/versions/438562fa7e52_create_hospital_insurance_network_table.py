"""create hospital_insurance_network table

Revision ID: 438562fa7e52
Revises: 368a6ece2e6d
Create Date: 2026-10-12 14:48:49.177537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '438562fa7e52'
down_revision: Union[str, Sequence[str], None] = '368a6ece2e6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('hospital_insurance_network',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('facility_id', sa.String(), nullable=False),
    sa.Column('operator_code', sa.String(), nullable=False),
    sa.Column('operator_name', sa.String(), nullable=True),
    sa.Column('has_emergency_coverage', sa.Boolean(), nullable=False),
    sa.Column('coverage_type', sa.String(), nullable=True),
    sa.Column('provider_relationship', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['facility_id'], ['hospitals.facility_id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('facility_id', 'operator_code', name='uq_hospital_operator')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('hospital_insurance_network')