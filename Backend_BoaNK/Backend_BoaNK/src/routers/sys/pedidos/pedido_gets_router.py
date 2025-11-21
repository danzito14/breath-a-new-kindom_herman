from sys import prefix
from typing import Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.pedidos.pedidos_estado import PedidoService_Gets

pedido_gets = APIRouter(prefix="/pedido_gets", tags=["Mostrar pedidos"])

@pedido_gets.get("/gets_pedidos", summary="Enviar pedidos")
def enviar_recibo(db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.get_pedidos_mesero()

@pedido_gets.get("/gets_pedidos_absolute", summary="Enviar pedidos")
def enviar_recibo(db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.get_pedidos_absolute()


@pedido_gets.get("/gets_pedidos_repartidor", summary="Enviar pedidos")
def enviar_recibo(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    id_ususario = current_user
    return  service.get_pedidos_repartidor(id_ususario)

@pedido_gets.get("/gets_pedidos_by_id_for_repartidor/{id_pedido}", summary="Enviar pedidos")
def enviar_recibo(id_pedido:str, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return  service.get_pedidos_by_id_for_repartidor(id_pedido)

@pedido_gets.get("/get_lista_platillo_by_id", summary="Para buscar por id")
def get_lista_by_id(id_detalle:str, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return service.get_platillos_by_id(id_detalle)

@pedido_gets.delete("/delete_platillo", summary="Cancela un platillo, si es el unico o el ultimo que faltaba en cancelar ccancela el pedido")
def cancelar_platillo(id_detalle: str, id_pedido: str, background_tasks: BackgroundTasks, id_mesa: Optional[str] = None, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db, background_tasks)
    return  service.cancelar_platillo(id_detalle, id_pedido, id_mesa)

@pedido_gets.delete("/cancelar_pedido", summary="Cancela un platillo, si es el unico o el ultimo que faltaba en cancelar ccancela el pedido")
def cancelar_platillo(id_pedido: str,  background_tasks: BackgroundTasks, id_mesa: Optional[str] = None, db: Session = Depends(get_db)):
    service = PedidoService_Gets(db, background_tasks)
    return  service.cancelar_pedido(id_pedido, id_mesa)

@pedido_gets.get("/lista_pendiente", summary="Lista de platillos pendientes  a cocinar para cocineros")
def lista_platillos_pendientes(db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return service.get_platillos_pendientes()

@pedido_gets.get("/lista_listo", summary="Lista de platillos pendientes  a cocinar para cocineros")
def lista_platillos_pendientes(db: Session = Depends(get_db)):
    service = PedidoService_Gets(db)
    return service.get_platillos_listos()

@pedido_gets.put("/actualizar_estado_platillo", summary="Cambiar el estado de un platillo")
def actualizar_estado_plato(id_detalle:str, estado:str, background_tasks: BackgroundTasks,
                            db:Session = Depends(get_db)):
    service = PedidoService_Gets(db, background_tasks)
    return service.cambiar_estatus(id_detalle, estado)

