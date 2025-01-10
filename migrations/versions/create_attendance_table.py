"""Create attendance table

Revision ID: create_attendance_table
Revises: 0bd45b51f4d6
Create Date: 2025-01-10 12:07:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_attendance_table'
down_revision = '0bd45b51f4d6'
branch_labels = None
depends_on = None


def upgrade():
    # Create attendance table
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
    # Drop attendance table
    op.drop_table('attendances')
