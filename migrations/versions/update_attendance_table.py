"""Update attendance table

Revision ID: update_attendance_table
Revises: create_attendance_table
Create Date: 2025-01-10 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_attendance_table'
down_revision = '0bd45b51f4d6'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing attendances table if it exists
    op.drop_table('attendances', if_exists=True)
    
    # Create new attendances table with correct schema
    op.create_table('attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lecture_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('marked_by_id', sa.Integer(), nullable=True),
        sa.Column('verification_method', sa.String(20), nullable=True),
        sa.Column('verification_data', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lecture_id'], ['lectures.id'], ),
        sa.ForeignKeyConstraint(['marked_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop the new attendances table
    op.drop_table('attendances')
