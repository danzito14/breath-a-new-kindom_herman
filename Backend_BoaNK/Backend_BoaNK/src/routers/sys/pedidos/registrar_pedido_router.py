from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.pedidos.registrar_pedido import CorreoResumen
from src.services.system.pedidos.registrar_pedido import RegistrarPedido_Service

registar = APIRouter(prefix="/registrar_pedido", tags=["Registrar pedido"])


@registar.post("/enviar_recibo", summary="Enviar recibo")
def enviar_recibo(
        data_correo: CorreoResumen,
        background_tasks: BackgroundTasks,  # 🔥 Agregar BackgroundTasks
        current_user: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level),
        db: Session = Depends(get_db)
):
    """
    Registra un pedido y envía notificaciones en tiempo real vía WebSocket

    - **id_temporal**: ID del pedido temporal
    - **direccion**: Dirección de entrega (opcional)
    - **metodo_pago**: Método de pago
    - **precio**: Total del pedido
    - **productos**: Lista de productos del pedido
    - **id_pedido**: ID del pedido existente (opcional, para agregar más productos)

    Notifica automáticamente a los cocineros conectados vía WebSocket
    """
    id_usuario = current_user
    nvl_usuario = nvl_usuario

    # 🔥 Pasar BackgroundTasks al servicio para poder enviar notificaciones WebSocket
    service = RegistrarPedido_Service(db, background_tasks)
    return service.pedido_main(id_usuario, nvl_usuario, data_correo)