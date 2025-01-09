#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance

# Initialize the database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
