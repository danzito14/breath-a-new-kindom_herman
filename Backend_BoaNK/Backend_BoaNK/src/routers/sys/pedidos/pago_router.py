from typing import Optional

from fastapi import  APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.pedidos.pago_service import Pago_Service


class pago_datos(BaseModel):
    id_pedido: str
    metodo_pago: str
    id_mesa: str
    referencia_pago: Optional[str] = None

pago_router = APIRouter(prefix="/pagar", tags=["Pagos"])

@pago_router.post("/pagar", summary="Pagar")
def pagar_pedido(data: pago_datos, current_user: str = Depends(get_current_user),  db: Session = Depends(get_db)):
    id_usuario= current_user
    service = Pago_Service(db)
    return service.registrar_pago(id_usuario,data.id_pedido, data.metodo_pago,data.id_mesa,data.referencia_pago)

@pago_router.get("/total_pedido", summary="Obtener el total del pedido")
def get_total_pedido(id_pedido:str, db: Session = Depends(get_db)):
    service = Pago_Service(db)
    return service.get_total_pedido(id_pedido)

@pago_router.get("/verificar_pedido", summary="Ver si ya esta terminado todo el pedido")
def verificar_pedido(id_pedido:str, db: Session = Depends(get_db)):
    service = Pago_Service(db)
    return service.verificar_estado_pedido(id_pedido)
