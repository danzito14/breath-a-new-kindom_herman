from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.tarjeta_tipotarjeta_schema import Tipos_TarjetasSchema, Tarjetas_PagoSchema
from src.services.repositories.tarjeta_tipotarjeta_service import Tarjetas_PagoService, Tipo_TarjetaService
from src.core.db_credentials import get_db

tarjetas = APIRouter()

@tarjetas.get("/")

@tarjetas.post("/tarjetas/create_tarjetas", summary="Crear una tarjeta")
def create_tarjetas(data: Tarjetas_PagoSchema, db: Session = Depends(get_db)):
    service = Tarjetas_PagoService(db)
    return  service.create_tarjetas_pago(data)

@tarjetas.get("/tarjetas/get_all_tarjetas/{id_usuario}", summary="Optener todas las tarjetas relacionadas a un usuaurio")
def get_all_tarjetas(id_usuario: str, db: Session = Depends(get_db)):
    service = Tarjetas_PagoService(db)
    return  service.get_all_tarjetas_pago(id_usuario)

@tarjetas.get("/tarjetas/get_tarjeta/{id_usuario}")
def get_tarjetas_by_usuario (id_usuario: str, titular: str, db: Session = Depends(get_db)):
    service = Tarjetas_PagoService(db)
    return service.get_tarjeta_pago_by_titular(id_usuario, titular)

@tarjetas.delete("/tarjetas/delete_tarjeta")
def delete_tarjeta (id_tarjeta: str, db: Session = Depends(get_db)):
    service = Tarjetas_PagoService(db)
    return  service.delete_tarjeta(id_tarjeta)

@tarjetas.post("/tarjetas/create_tipo_tarjeta", summary="Crear un nuevo tipo de tarjeta")
def create_tipo_tarjeta (data: Tipos_TarjetasSchema, db: Session = Depends(get_db)):
    service = Tipo_TarjetaService(db)
    return service.create_tipo_tarjetas(data)

@tarjetas.get("/tarjetas/get_all_tipo", summary="Mostrar todos los tipos")
def get_all_tipo_tarjeta(db: Session = Depends(get_db)):
    service = Tipo_TarjetaService(db)
    return service.get_all_tipo_tarjetas()

@tarjetas.delete("/tarjetas/delete_tipo")
def delete_tipo_tajeta (id_tipo_tarjeta: int, db: Session = Depends(get_db)):
    service = Tipo_TarjetaService(db)
    return service.delete_tipo_tarjeta(id_tipo_tarjeta)

