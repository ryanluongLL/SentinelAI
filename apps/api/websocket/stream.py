import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from services.simulator import generate_event_stream

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.active_connections.remove(connection)

manager = ConnectionManager()

async def stream_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        async for event in generate_event_stream(attack_probability=0.2):
            await manager.broadcast({
                "type": "network_event",
                "data": event
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
