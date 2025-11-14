from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.core.websocket_manager import manager

ws_router = APIRouter()


@ws_router.websocket("/ws/{role}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, role: str, user_id: str):
    """
    Roles válidos: cocina, meseros, admin, cliente
    """
    await manager.connect(websocket, role)

    try:
        while True:
            # Mantener conexión activa
            data = await websocket.receive_text()

            # Aquí puedes manejar mensajes del cliente si es necesario
            # Por ejemplo, confirmaciones de recepción

    except WebSocketDisconnect:
        manager.disconnect(websocket, role)
        print(f"Cliente {user_id} desconectado del rol {role}")