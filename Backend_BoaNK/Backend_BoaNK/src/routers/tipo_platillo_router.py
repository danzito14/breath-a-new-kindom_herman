from fastapi import  APIRouter, Depends, Body
from sqlalchemy.orm import Session

from src.schemas.tipo_platillo_schema import Tipo_platilloSchema
from src.services.tipo_platillo_service import Tipo_platillosService
from src.core.db_credentials import get_db

tipo_platillos = APIRouter()

@tipo_platillos.get("/")
def root():
    return {"message":"Ruta Tipo platillos"}

@tipo_platillos.post("/tipo_platillos/create_tipo_platillo", summary="Agregar un tipo platillo nuevo")
def create_tipo_platillo(data:Tipo_platilloSchema, db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return service.create_tipo_platillo(data)

@tipo_platillos.get("/tipo_platillos/get_all_tipo_platillos")
def get_all_tipo_platillos(db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return  service.get_all_tipo_platillo()

@tipo_platillos.put("/tipo_platillos/update_tipo_platillo/{id_tipo_platillo}")
def update_tipo_platillo(id_tipo_platillo: int, data : dict = Body(...), db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return service.update_tipo_platillo(id_tipo_platillo, data)

@tipo_platillos.delete("/tipo_platillos/delete_tipo_platillos/{id_tipo_platillo}")
def delete_tipo_platillo(id_tipo_platillo: int, db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return  service.delete_favorito(id_tipo_platillo)



