from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, match_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(match_id, []).append(websocket)

    def disconnect(self, match_id: int, websocket: WebSocket):
        if match_id in self.active_connections:
            if websocket in self.active_connections[match_id]:
                self.active_connections[match_id].remove(websocket)

    async def broadcast(self, match_id: int, message: dict):
        connections = self.active_connections.get(match_id, [])
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()