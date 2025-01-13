# Exit on error
$ErrorActionPreference = "Stop"

Write-Host "Initializing database..."

# Export Flask app
$env:FLASK_APP = "wsgi.py"

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

Write-Host "Database initialized successfully!"
