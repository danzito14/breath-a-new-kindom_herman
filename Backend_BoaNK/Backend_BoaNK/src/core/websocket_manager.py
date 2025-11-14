from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Almacena las conexiones activas por tipo de usuario
        self.active_connections: Dict[str, List[WebSocket]] = {
            "cocineros": [],
            "meseros": [],
            "admin": []
        }

    async def connect(self, websocket: WebSocket, user_type: str):
        """Acepta una nueva conexión WebSocket"""
        await websocket.accept()
        if user_type in self.active_connections:
            self.active_connections[user_type].append(websocket)
            logger.info(f"Nueva conexión {user_type}. Total: {len(self.active_connections[user_type])}")
        else:
            logger.warning(f"Tipo de usuario desconocido: {user_type}")

    def disconnect(self, websocket: WebSocket, user_type: str):
        """Elimina una conexión WebSocket"""
        if user_type in self.active_connections:
            if websocket in self.active_connections[user_type]:
                self.active_connections[user_type].remove(websocket)
                logger.info(f"Desconexión {user_type}. Total: {len(self.active_connections[user_type])}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envía un mensaje a una conexión específica"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error al enviar mensaje personal: {e}")

    async def broadcast_to_group(self, message: dict, user_type: str):
        """Envía un mensaje a todos los usuarios de un tipo específico"""
        if user_type not in self.active_connections:
            logger.warning(f"Tipo de usuario no existe: {user_type}")
            return

        disconnected = []
        for connection in self.active_connections[user_type]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error al enviar mensaje a {user_type}: {e}")
                disconnected.append(connection)

        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn, user_type)

    async def broadcast_to_all(self, message: dict):
        """Envía un mensaje a todos los usuarios conectados"""
        for user_type in self.active_connections:
            await self.broadcast_to_group(message, user_type)

    def get_connections_count(self, user_type: str = None) -> int:
        """Obtiene el número de conexiones activas"""
        if user_type:
            return len(self.active_connections.get(user_type, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Instancia global del gestor de conexiones
manager = ConnectionManager()