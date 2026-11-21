"""add persistent credential session version to users

Revision ID: f7c8d9e0a1b2
Revises: e1a2b3c4d5e6
Create Date: 2026-11-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'f7c8d9e0a1b2'
down_revision = 'e1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('session_version', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade():
    op.drop_column('users', 'session_version')
