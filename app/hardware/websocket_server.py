import asyncio
import websockets
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WebSocketServer')

class HardwareServer:
    def __init__(self):
        self.clients = set()
        self.esp8266_client = None
        self.fingerprint_status = "Not Ready"
        self.rfid_status = "Not Ready"
        self.fingerprint_count = 0
        self.rfid_count = 0

    async def register(self, websocket):
        self.clients.add(websocket)
        logger.info(f"New client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket):
        self.clients.remove(websocket)
        if websocket == self.esp8266_client:
            self.esp8266_client = None
            self.fingerprint_status = "Not Ready"
            self.rfid_status = "Not Ready"
            await self.broadcast_status()
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast_status(self):
        """Broadcast current hardware status to all clients"""
        status_message = {
            "type": "status",
            "controller": self.esp8266_client is not None,
            "fingerprint": self.fingerprint_status == "Ready",
            "rfid": self.rfid_status == "Ready",
            "timestamp": datetime.now().isoformat()
        }
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(status_message)) for client in self.clients]
            )

    async def handle_esp8266_message(self, message, websocket):
        """Handle messages from ESP8266"""
        try:
            data = json.loads(message)
            if "device" in data and data["device"] == "esp8266":
                if self.esp8266_client is None:
                    self.esp8266_client = websocket
                    logger.info("ESP8266 connected")
                
                if "status" in data:
                    self.fingerprint_status = data["status"].get("fingerprint", "Not Ready")
                    self.rfid_status = data["status"].get("rfid", "Not Ready")
                    self.fingerprint_count = data["status"].get("fingerprint_count", 0)
                    self.rfid_count = data["status"].get("rfid_count", 0)
                    await self.broadcast_status()
                
                elif "event" in data:
                    event_data = data["event"]
                    event_type = event_data.get("type")
                    
                    if event_type == "fingerprint":
                        await self.handle_fingerprint_event(event_data)
                    elif event_type == "rfid":
                        await self.handle_rfid_event(event_data)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from ESP8266")
        except Exception as e:
            logger.error(f"Error handling ESP8266 message: {e}")

    async def handle_fingerprint_event(self, event_data):
        """Handle fingerprint scanner events"""
        message = {
            "type": "fingerprint",
            "status": event_data.get("status"),
            "message": event_data.get("message"),
            "count": self.fingerprint_count,
            "timestamp": datetime.now().isoformat()
        }
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients]
            )

    async def handle_rfid_event(self, event_data):
        """Handle RFID reader events"""
        message = {
            "type": "rfid",
            "status": event_data.get("status"),
            "cardId": event_data.get("card_id"),
            "count": self.rfid_count,
            "timestamp": datetime.now().isoformat()
        }
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients]
            )

    async def handle_client_message(self, message, websocket):
        """Handle messages from web clients"""
        try:
            data = json.loads(message)
            command = data.get("command")
            
            if self.esp8266_client is None:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "ESP8266 not connected"
                }))
                return
            
            # Forward command to ESP8266
            await self.esp8266_client.send(json.dumps({
                "command": command,
                "timestamp": datetime.now().isoformat()
            }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    async def handler(self, websocket, path):
        """Handle new WebSocket connections"""
        await self.register(websocket)
        try:
            async for message in websocket:
                if websocket == self.esp8266_client:
                    await self.handle_esp8266_message(message, websocket)
                else:
                    await self.handle_client_message(message, websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

async def main():
    hardware_server = HardwareServer()
    async with websockets.serve(hardware_server.handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
