from fastapi import Body, APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.puesto_schema import PuestoSchema
from src.services.repositories.puesto_service import PuestoService
from src.core.db_credentials import get_db

puestos = APIRouter(tags=["Puesto"])

@puestos.get("/")
def root():
    return {"message": "Ruta default"}

@puestos.post("/puestos/create_puesto")
def create_puesto(data: PuestoSchema, db: Session = Depends(get_db)):
    service = PuestoService(db)
    return service.create_puesto(data)

@puestos.get("/puestos/get_all_puestos")
def get_all_puestos(db: Session = Depends(get_db)):
    service = PuestoService(db)
    return service.get_all_puestos()

@puestos.get("/puestos/get_puesto")
def get_puesto(id_puesto: int, db: Session = Depends(get_db)):
    service = PuestoService(db)
    return service.get_puesto(id_puesto)

@puestos.put("/puestos/update_puesto/{id_puesto}")
def update_puesto(id_puesto: int, data: dict = Body(...), db: Session = Depends(get_db)):
    service = PuestoService(db)
    return service.update_puesto(id_puesto, data)
