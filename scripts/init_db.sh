#!/bin/bash

# Exit on error
set -e

echo "Initializing database..."

# Export Flask app
export FLASK_APP=wsgi.py

# Drop all tables (if they exist)
python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.drop_all()
"

# Run migrations
flask db upgrade

echo "Database initialized successfully!"
