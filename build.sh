#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Create instance folder
mkdir -p instance

# Run database migrations if needed
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
