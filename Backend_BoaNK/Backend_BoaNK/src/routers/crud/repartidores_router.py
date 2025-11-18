from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.jwt_managger import get_current_user
from src.schemas.pedidos.repartidor_schema import RepartidorSchema
from src.services.repositories.repartidores_service import RepartidoresService
from src.core.db_credentials import get_db

_repartidores = APIRouter(prefix="/repartidores", tags=["Repartidores"])

@_repartidores.post("/cocineros/create_cocinero", summary="Crea un nuevo cocinero")
def create_repartidores(data: RepartidorSchema, db: Session = Depends(get_db)):
    service = RepartidoresService(db)
    return service.create_repartidor(data)

@_repartidores.put("/cocineros/get_all_repartidores", summary="Obtener todos los cocineros")
def get_all_repartidores(db:Session = Depends(get_db)):
    service = RepartidoresService(db)
    return service.get_all_repartidores()

@_repartidores.put("/cocineros/update_cocinero", summary="Actualizar cocinero")
def update_cocinero(data:dict,current_user: str = Depends(get_current_user), db:Session = Depends(get_db)):
    service = RepartidoresService(db)
    id_usuario = current_user
    return service.update_repartidores(id_usuario, data)