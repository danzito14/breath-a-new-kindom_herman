from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.jwt_managger import get_current_user
from src.schemas.direcciones_usuario_schema import Direcciones_usuarioSchema
from src.services.repositories.direcciones_usuario_service import Direcciones_usuarioService
from src.core.db_credentials import get_db

direcciones =APIRouter(tags=["Direccion usuario"])


@direcciones.get("/")
def root():
    return {"message":"Ruta de platillos direcciones"}

@direcciones.post("/direcciones/create_direccion", summary="Agregar un platillo a direcciones")
def create_direcciones(data:Direcciones_usuarioSchema, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    data.id_usuario = current_user
    service = Direcciones_usuarioService(db)
    return  service.create_direcciones_usuario(data)

@direcciones.get("/direcciones/get_all_direcciones")
def get_all_direcciones(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    id_usuario = current_user
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