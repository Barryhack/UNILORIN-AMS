"""Production server using Waitress."""
import os
from waitress import serve
from dotenv import load_dotenv
from app import create_app
from config import ProductionConfig

# Load environment variables
load_dotenv()

# Create Flask application instance
app = create_app(ProductionConfig)

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8000))
    
    # Run the application with Waitress
    serve(app, host='0.0.0.0', port=port, threads=4)
