"""add_document_chunks_table

Revision ID: e8ffb590bb5c
Revises: 28d5e76d5097
Create Date: 2026-09-06 17:52:10.484882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = 'e8ffb590bb5c'
down_revision: Union[str, Sequence[str], None] = '28d5e76d5097'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_index(
        'document_chunks_embedding_idx',
        'document_chunks',
        ['embedding'],
        postgresql_using='ivfflat',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
        postgresql_with={'lists': '100'},
    )


def downgrade() -> None:
    op.drop_index('document_chunks_embedding_idx', table_name='document_chunks')
    op.drop_table('document_chunks')