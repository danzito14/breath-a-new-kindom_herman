from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.direcciones_usuario_schema import Direcciones_usuarioSchema
from src.services.direcciones_usuario_service import Direcciones_usuarioService
from src.core.db_credentials import get_db

direcciones =APIRouter()


@direcciones.get("/")
def root():
    return {"message":"Ruta de platillos direcciones"}

@direcciones.post("/direcciones/create_direccion", summary="Agregar un platillo a direcciones")
def create_direcciones(data:Direcciones_usuarioSchema, db: Session = Depends(get_db)):
    service = Direcciones_usuarioService(db)
    return  service.create_direcciones_usuario(data)

@direcciones.get("/direcciones/get_all_direcciones/{id_usuario}")
def get_all_direcciones(id_usuario: str, db: Session = Depends(get_db)):
    service = Direcciones_usuarioService(db)
    return  service.get_all_direcciones_usuario(id_usuario)

@direcciones.get("/direcciones/get_direccion/")
def get_direccion(id_usuario:str, alias: str, db: Session = Depends(get_db)):
    service = Direcciones_usuarioService(db)
    return service.get_direccion_usuario(id_usuario, alias)

@direcciones.put("/direcciones/update_direccion/{id_direccion}")
def update_direccion(id_direccion:str,  data: dict, db:Session = Depends(get_db)):
    service = Direcciones_usuarioService(db)
    return service.update_direccion_usuario(id_direccion, data)

@direcciones.delete("/direcciones/delete_direccion/{id_direccion}", summary="Eliminar un platillo de direcciones")
def delete_direcciones(id_direccion: str, db: Session = Depends(get_db)):
    service = Direcciones_usuarioService(db)
    return service.delete_direcciones_usuario(id_direccion)