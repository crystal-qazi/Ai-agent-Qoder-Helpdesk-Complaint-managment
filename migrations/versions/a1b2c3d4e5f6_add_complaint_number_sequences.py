"""add transactional complaint number sequences

Revision ID: a1b2c3d4e5f6
Revises: f7c8d9e0a1b2
Create Date: 2026-11-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f7c8d9e0a1b2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'complaint_number_sequences',
        sa.Column('year', sa.Integer(), primary_key=True),
        sa.Column('next_number', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade():
    op.drop_table('complaint_number_sequences')
