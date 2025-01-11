"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import ProductionConfig

app = create_app(ProductionConfig)

# Ensure all models are registered
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
