from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.core.websocket_manager import manager
import logging

logger = logging.getLogger(__name__)

websocket_router = APIRouter(prefix="/ws", tags=["WebSocket"])


@websocket_router.websocket("/connect")
async def websocket_endpoint(
        websocket: WebSocket,
        user_type: str = Query(..., description="Tipo de usuario: cocineros, meseros, admin")
):
    """
    Endpoint WebSocket para conectar usuarios.

    Parámetros:
    - user_type: 'cocineros', 'meseros' o 'admin'

    Ejemplo de conexión desde frontend:
    ws://localhost:8000/ws/connect?user_type=cocineros
    """
    await manager.connect(websocket, user_type)

    try:
        # Enviar mensaje de bienvenida
        await manager.send_personal_message({
            "tipo": "conexion_exitosa",
            "mensaje": f"Conectado como {user_type}",
            "timestamp": str(websocket)
        }, websocket)

        # Mantener la conexión abierta y escuchar mensajes
        while True:
            data = await websocket.receive_json()
            logger.info(f"Mensaje recibido de {user_type}: {data}")

            # Puedes manejar diferentes tipos de mensajes aquí
            if data.get("tipo") == "ping":
                await manager.send_personal_message({
                    "tipo": "pong",
                    "timestamp": data.get("timestamp")
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_type)
        logger.info(f"Cliente {user_type} desconectado")
    except Exception as e:
        logger.error(f"Error en WebSocket: {e}")
        manager.disconnect(websocket, user_type)


@websocket_router.get("/status")
async def get_websocket_status():
    """Endpoint para verificar el estado de las conexiones WebSocket"""
    return {
        "cocineros_conectados": manager.get_connections_count("cocineros"),
        "meseros_conectados": manager.get_connections_count("meseros"),
        "admin_conectados": manager.get_connections_count("admin"),
        "total_conexiones": manager.get_connections_count()
    }