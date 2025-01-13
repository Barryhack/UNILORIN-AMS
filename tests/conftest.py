import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from config import TestingConfig

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(TestingConfig)
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(client):
    """A test client with authentication."""
    # Create a test user
    with client.application.app_context():
        user = User(
            email='test@example.com',
            name='Test User',
            role='admin'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Log in
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    return client
