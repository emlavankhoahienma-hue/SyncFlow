import asyncio
import json
from typing import List, Set
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast_json(self, data: dict):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_progress(self, transfer_id: str, sent: int, total: int, speed_bps: float, eta_s: float):
        payload = {
            "type": "progress",
            "transfer_id": transfer_id,
            "sent": sent,
            "total": total,
            "speed_bps": round(speed_bps, 2),
            "eta_s": round(eta_s, 1)
        }
        await self.broadcast_json(payload)

    async def send_done(self, transfer_id: str, path: str):
        payload = {
            "type": "done",
            "transfer_id": transfer_id,
            "path": str(path)
        }
        await self.broadcast_json(payload)

    async def send_error(self, transfer_id: str, message: str):
        payload = {
            "type": "error",
            "transfer_id": transfer_id,
            "message": message
        }
        await self.broadcast_json(payload)

ws_manager = ConnectionManager()
