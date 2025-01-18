"""add dashboard features

Revision ID: add_dashboard_features
Revises: previous_revision
Create Date: 2025-01-18 19:19:32.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_dashboard_features'
down_revision = None  # Update this with your last migration's revision ID
branch_labels = None
depends_on = None

def upgrade():
    # Update courses table
    op.alter_column('courses', 'semester',
        existing_type=sa.String(20),
        type_=sa.String(6),
        existing_nullable=True)
    
    op.add_column('courses',
        sa.Column('minimum_attendance', sa.Integer(), nullable=False, server_default='75'))

def downgrade():
    # Revert courses table changes
    op.alter_column('courses', 'semester',
        existing_type=sa.String(6),
        type_=sa.String(20),
        existing_nullable=True)
    
    op.drop_column('courses', 'minimum_attendance')
