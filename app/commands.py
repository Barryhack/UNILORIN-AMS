"""Flask CLI commands."""
import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.department import Department, create_default_departments
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database."""
    try:
        # Create all tables
        db.create_all()
        click.echo('Created all database tables.')

        # Create default departments
        create_default_departments()
        click.echo('Created default departments.')

        # Create default admin user if it doesn't exist
        if not User.query.filter_by(login_id='ADMIN001').first():
            # Get Computer Science department
            cs_dept = Department.query.filter_by(code='CSC').first()
            if not cs_dept:
                cs_dept = Department(
                    name='Computer Science',
                    code='CSC',
                    description='Department of Computer Science'
                )
                db.session.add(cs_dept)
                db.session.commit()

            admin = User(
                login_id='ADMIN001',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.password = 'admin123'  # This will be hashed
            admin.department_id = cs_dept.id
            db.session.add(admin)
            db.session.commit()
            click.echo('Created default admin user.')
        else:
            click.echo('Default admin user already exists.')

        click.echo('Database initialization completed successfully.')
    except Exception as e:
        logger.error(f'Error initializing database: {str(e)}')
        click.echo('Error initializing database. Check the logs for details.', err=True)
        raise
