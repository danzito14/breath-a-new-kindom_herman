
from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session


from src.core.jwt_managger import  get_current_user
from src.schemas.pedidos.pedidostemporal_schema import pedido_temporalSchema
from src.services.system.pedidos.pedidos_temporal_service import PedidoTemporalService
from src.core.db_credentials import get_db

temporal = APIRouter(prefix="/carrito_temporal", tags=["Carrito temporal"])

# --- Crear o reemplazar carrito temporal ---
@temporal.post("/guardar")
def guardar_carrito(data: pedido_temporalSchema,current_user: str = Depends(get_current_user),  db: Session = Depends(get_db)):
    data.id_usuario = current_user
    service = PedidoTemporalService(db)
    return service.create_or_update_temporal(data)

@temporal.get("/get_resumen", summary="Obtener el resumen del pedido")
def get_resumen(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    id_usuario = current_user
    service = PedidoTemporalService(db)
    return service.get_temporal(id_usuario)

@temporal.put("/update_resumen", summary="Añadir lo que falta")
def update_resumen(data:dict, current_user: str = Depends(get_current_user), db: Session =Depends(get_db) ):
    id_usuario = current_user
    service = PedidoTemporalService(db)
    return  service.update_temporal(id_usuario, data)

