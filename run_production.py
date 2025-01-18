"""Production server script using Waitress."""
import os
import logging
from waitress import serve
from dotenv import load_dotenv
from app import create_app
from config import ProductionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/production.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Run the production server."""
    try:
        # Load environment variables
        load_dotenv()

        # Set production environment
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = '0'

        # Create Flask application instance
        app = create_app(ProductionConfig)

        # Get port from environment variable or use default
        port = int(os.environ.get('PORT', 8000))
        
        logger.info(f"Starting production server on port {port}")
        
        # Run the application with Waitress
        serve(
            app,
            host='0.0.0.0',
            port=port,
            threads=4,
            url_scheme='https'
        )
    except Exception as e:
        logger.error(f"Error starting production server: {e}")
        raise

if __name__ == '__main__':
    main()
