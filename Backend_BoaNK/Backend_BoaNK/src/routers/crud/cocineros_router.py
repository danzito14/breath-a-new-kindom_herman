from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.cocineros_schemas import CocinaSchema
from src.services.repositories.Cocineros_service import CocinerosService
from src.core.db_credentials import get_db

_cocineros = APIRouter(tags=["Cocineros"])

@_cocineros.get("/")
def root():
    return {"message":"Ruta default"}

@_cocineros.post("/cocineros/create_cocinero", summary="Crea un nuevo cocinero")
def create_cocineros(data: CocinaSchema, db: Session = Depends(get_db)):
    service = CocinerosService(db)
    return service.create_cocinero(data)

@_cocineros.put("/cocineros/get_all_cocineros", summary="Obtener todos los cocineros")
def get_all_cocineros(db:Session = Depends(get_db)):
    service = CocinerosService(db)
    return service.get_all_cocina()

@_cocineros.put("/cocineros/update_cocinero", summary="Actualizar cocinero")
def update_cocinero(id_empleado: str, data:dict, db:Session = Depends(get_db)):
    service = CocinerosService(db)
    return service.update_cocinero(id_empleado, data)