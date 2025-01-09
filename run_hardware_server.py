import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from hardware.websocket_server import main
import asyncio

if __name__ == "__main__":
    print("Starting Hardware WebSocket Server...")
    print("Listening on ws://0.0.0.0:8765")
    asyncio.run(main())
