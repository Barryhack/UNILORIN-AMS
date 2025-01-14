"""Application entry point."""
from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
