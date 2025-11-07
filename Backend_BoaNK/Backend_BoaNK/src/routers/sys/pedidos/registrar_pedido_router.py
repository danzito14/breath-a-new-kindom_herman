from sys import prefix

from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.pedidos.registrar_pedido import Producto, CorreoResumen
from src.services.system.pedidos.registrar_pedido import RegistrarPedido_Service

registar = APIRouter(prefix="/registrar_pedido", tags=["Registrar pedido"])

@registar.post("/enviar_recibo", summary="Enviar recibo")
def enviar_recibo(data_correo: CorreoResumen,current_user: str = Depends(get_current_user),
                  nvl_usuario: str = Depends(get_user_level), db: Session = Depends(get_db)):
    id_usurio = current_user
    nvl_usuario = nvl_usuario
    service = RegistrarPedido_Service(db)
    return service.pedido_main(id_usurio,nvl_usuario, data_correo)
