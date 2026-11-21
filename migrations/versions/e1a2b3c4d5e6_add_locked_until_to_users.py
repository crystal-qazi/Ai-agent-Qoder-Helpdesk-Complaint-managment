"""add locked_until to users for temporary lockout

Revision ID: e1a2b3c4d5e6
Revises: da2a5c2ebb10
Create Date: 2026-11-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1a2b3c4d5e6'
down_revision = 'da2a5c2ebb10'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'locked_until')
