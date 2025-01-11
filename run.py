"""Application entry point."""
import os
from app import create_app
from config import DevelopmentConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    app = create_app(DevelopmentConfig)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
