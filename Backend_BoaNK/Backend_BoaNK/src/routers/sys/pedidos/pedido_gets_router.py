from sys import prefix

from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.pedidos.pedidos_estado import PedidoService_Gets

pedido_gets = APIRouter(prefix="/pedido_gets", tags=["Mostrar pedidos"])

@pedido_gets.get("/gets_pedidos", summary="Enviar pedidos")
def enviar_recibo(db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.get_pedidos_mesero()

@pedido_gets.delete("/delete_platillo", summary="Cancela un platillo, si es el unico o el ultimo que faltaba en cancelar ccancela el pedido")
def cancelar_platillo(id_detalle: str, id_pedido: str, id_mesa:str, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.cancelar_platillo(id_detalle, id_pedido, id_mesa)

@pedido_gets.delete("/cancelar_pedido", summary="Cancela un platillo, si es el unico o el ultimo que faltaba en cancelar ccancela el pedido")
def cancelar_platillo(id_pedido: str, id_mesa:str, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.cancelar_pedido(id_pedido, id_mesa)