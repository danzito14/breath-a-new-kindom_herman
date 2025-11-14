from fastapi import WebSocket
from typing import Dict, List
import json


class ConnectionManager:
    def __init__(self):
        # Conexiones por rol: cocina, meseros, admin
        self.active_connections: Dict[str, List[WebSocket]] = {
            "cocina": [],
            "meseros": [],
            "admin": [],
            "cliente": []
        }

    async def connect(self, websocket: WebSocket, role: str):
        await websocket.accept()
        if role in self.active_connections:
            self.active_connections[role].append(websocket)

    def disconnect(self, websocket: WebSocket, role: str):
        if role in self.active_connections:
            self.active_connections[role].remove(websocket)

    async def send_to_role(self, role: str, message: dict):
        """Envía mensaje a todos los conectados de un rol específico"""
        for connection in self.active_connections.get(role, []):
            try:
                await connection.send_json(message)
            except:
                pass

    async def broadcast(self, message: dict):
        """Envía a todos los roles"""
        for role_connections in self.active_connections.values():
            for connection in role_connections:
                try:
                    await connection.send_json(message)
                except:
                    pass


# Instancia global
manager = ConnectionManager()