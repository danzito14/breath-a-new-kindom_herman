from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.mesa_schema import MesaSchema
from src.services.repositories.mesa_service import  MesaService
from src.core.db_credentials import get_db

mesas = APIRouter(tags=["Mesa"])

@mesas.get("/")
def root():
    return {"message": "Ruta default"}

@mesas.post("/mesas/create_mesa", summary="Registra una mesa")
def create_mesa (data: MesaSchema, db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.create_mesa(data)

@mesas.get("/mesas/get_all_mesas", summary="Obten todas las mesas")
def get_all_mesas (db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.get_all_mesas()

@mesas.get("/mesas/get_all_mesas_ocupadas", summary="Obten todas las mesas")
def get_all_mesas (db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.get_all_mesas_ocupadas()


@mesas.get("/mesas/get_mesa/{Nombre_mesa}", summary="Obtener una mesa")
def get_mesa (Nombre_mesa: str, db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.get_mesa(Nombre_mesa)

@mesas.put("/mesas/update_mesa/{id_mesa}")
def update_mesa (id_mesa: str, data:dict, db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.update_mesa(id_mesa, data)

@mesas.delete("/mesas/delete_mesa/")
def delte_mesa (id_mesa: str,db:Session = Depends(get_db)):
    service = MesaService(db)
    return  service.delete_mesa(id_mesa)