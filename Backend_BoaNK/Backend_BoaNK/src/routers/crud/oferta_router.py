from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.ofertas_schema import OfertasSchema, Oferta_PlatilloSchema
from src.services.repositories.ofertas_service import OfertasService, Oferta_PlatilloService
from src.core.db_credentials import get_db

ofertas = APIRouter()


@ofertas.post("/ofertas/create_oferta", summary="Crear una nueva oferta")
def create_oferta (data: OfertasSchema, db:Session = Depends(get_db)):
    service = OfertasService(db)
    return service.create_oferta(data)

@ofertas.get("/ofertas/get_all_ofertas", summary="Obtener todas las ofertas")
def get_all_ofertas(db:Session = Depends(get_db)):
    service = OfertasService(db)
    return service.get_all_ofertas()

@ofertas.get("/ofertas/get_oferta/{nombre_oferta}", summary="Obtener una sola oferta")
def get_oferta(descripcion: str, db: Session = Depends(get_db)):
    service = OfertasService(db)
    return service.get_oferta(descripcion)
@ofertas.get("/ofertas/get_ofertas_for_home", summary="Obtener todos los platillo oferta para el home")
def get_all_ofertas_platillos_home(db:Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.get_all_platillos_on_oferta_home()

@ofertas.put("/ofertas/update_oferta/{id_oferta}", summary="Actualizar oferta")
def update_oferta (id_oferta:str, data:dict, db: Session = Depends(get_db)):
    service = OfertasService(db)
    return service.update_oferta(id_oferta, data)


@ofertas.post("/ofertas/create_oferta_platillo/", summary="Agregar platillos a una oferta")
def create_oferta_platillos (data: Oferta_PlatilloSchema,db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.create_oferta_platillo(data)

@ofertas.get("/ofertas/get_all_ofertas_platillos", summary="Obtener todos los platilos de todas las ofertas")
def get_all_ofertas_platillo(db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.get_all_ofertas_platillos()

@ofertas.get("/ofertas/get_oferta_platillo/{id_oferta}", summary="Obtener los platillos de una oferta")
def get_platillos_by_oferta (id_oferta:str, db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.get_platillos_oferta(id_oferta)

@ofertas.post("/ofertas/add_platillos_oferta/{id_oferta}", summary="Agregar uno o más platillos a una oferta")
def add_platillos_oferta(id_oferta:str, nuevos_platillos: List[Oferta_PlatilloSchema], db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.add_varios_platillos_a_oferta(id_oferta, nuevos_platillos)

@ofertas.delete("/ofertas/delete_platillo_oferta/")
def delete_platillo_oferta(id_oferta_platillo:str,db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.delete_oferta_platillo(id_oferta_platillo)

@ofertas.delete("/ofertas/delete_all_platillo_oferta")
def delete_all_platillo_oferta (id_oferta: str, db: Session = Depends(get_db)):
    service = Oferta_PlatilloService(db)
    return service.delete_todos_platillos_oferta_platillo(id_oferta)
