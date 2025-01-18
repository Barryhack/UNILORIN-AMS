"""add dashboard features

Revision ID: add_dashboard_features
Revises: a8a88da83c1e
Create Date: 2025-01-18 19:19:32.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_dashboard_features'
down_revision = 'a8a88da83c1e'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns first
    op.add_column('courses',
        sa.Column('minimum_attendance', sa.Integer(), server_default='75', nullable=False))
    
    # Create a temporary column for the new semester format
    op.add_column('courses',
        sa.Column('new_semester', sa.String(6), nullable=True))
    
    # Update the new semester column with converted data
    connection = op.get_bind()
    courses_table = sa.Table(
        'courses',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('semester', sa.String(20)),
        sa.Column('new_semester', sa.String(6))
    )
    
    for course in connection.execute(courses_table.select()):
        if course.semester:
            # Convert semester format (e.g., "Fall 2023" to "202309")
            old_semester = course.semester.strip().lower()
            year = ''.join(filter(str.isdigit, old_semester))
            if 'fall' in old_semester:
                month = '09'
            elif 'spring' in old_semester:
                month = '02'
            else:
                month = '01'
            new_semester = f"{year}{month}" if year else None
            
            if new_semester:
                connection.execute(
                    courses_table.update().
                    where(courses_table.c.id == course.id).
                    values(new_semester=new_semester)
                )
    
    # Drop old semester column
    op.drop_column('courses', 'semester')
    
    # Rename new_semester to semester
    op.alter_column('courses', 'new_semester',
        new_column_name='semester',
        existing_type=sa.String(6),
        nullable=True)

def downgrade():
    # Create a temporary column for the old semester format
    op.add_column('courses',
        sa.Column('old_semester', sa.String(20), nullable=True))
    
    # Convert back to the old format
    connection = op.get_bind()
    courses_table = sa.Table(
        'courses',
        sa.MetaData(),
        sa.Column('id', sa.Integer),
        sa.Column('semester', sa.String(6)),
        sa.Column('old_semester', sa.String(20))
    )
    
    for course in connection.execute(courses_table.select()):
        if course.semester:
            # Convert YYYYMM to "Season YYYY"
            year = course.semester[:4]
            month = course.semester[4:]
            if month == '09':
                season = 'Fall'
            elif month == '02':
                season = 'Spring'
            else:
                season = 'Unknown'
            old_semester = f"{season} {year}"
            
            connection.execute(
                courses_table.update().
                where(courses_table.c.id == course.id).
                values(old_semester=old_semester)
            )
    
    # Drop new semester column
    op.drop_column('courses', 'semester')
    
    # Rename old_semester to semester
    op.alter_column('courses', 'old_semester',
        new_column_name='semester',
        existing_type=sa.String(20),
        nullable=True)
    
    # Drop minimum_attendance column
    op.drop_column('courses', 'minimum_attendance')
