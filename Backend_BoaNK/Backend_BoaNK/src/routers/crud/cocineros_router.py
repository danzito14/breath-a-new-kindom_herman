from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.jwt_managger import get_current_user
from src.schemas.cocineros_schemas import CocinaSchema
from src.services.repositories.Cocineros_service import CocinerosService
from src.core.db_credentials import get_db

_cocineros = APIRouter(tags=["Cocineros"])

@_cocineros.get("/cocineros/tiene_plato", summary="Ver si tiene plato para ver si le damos uno o no")
def tiene_plato(curren_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    service = CocinerosService(db)
    id_usuario = curren_user
    return  service.tiene_plato(id_usuario)

@_cocineros.get("/cocineros/asignar_plato", summary="Ver si tiene plato para ver si le damos uno o no")
def tiene_plato(curren_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    service = CocinerosService(db)
    id_usuario = curren_user
    return  service.asignar_plato(id_usuario)

@_cocineros.post("/cocineros/create_cocinero", summary="Crea un nuevo cocinero")
def create_cocineros(data: CocinaSchema, db: Session = Depends(get_db)):
    service = CocinerosService(db)
    return service.create_cocinero(data)

@_cocineros.put("/cocineros/get_all_cocineros", summary="Obtener todos los cocineros")
def get_all_cocineros(db:Session = Depends(get_db)):
    service = CocinerosService(db)
    return service.get_all_cocina()

@_cocineros.put("/cocineros/update_cocinero", summary="Actualizar cocinero")
def update_cocinero(data:dict,current_user: str = Depends(get_current_user), db:Session = Depends(get_db)):
    service = CocinerosService(db)
    id_usuario = current_user
    return service.update_cocinero(id_usuario, data)

@_cocineros.put("/cocineros/update_cocinero_plato", summary="Actualizar el plato que esta cocinando el cocinero")
def update_cocinero(data:dict,current_user: str = Depends(get_current_user), db:Session = Depends(get_db)):
    service = CocinerosService(db)
    id_usuario = current_user
    return service.update_cocinero_plato(id_usuario, data)