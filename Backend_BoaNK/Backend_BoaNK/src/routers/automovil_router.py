from fastapi import Body, APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.automovil_schema import AutomovilSchema
from src.services.automovil_service import AutomovilService
from src.core.db_credentials import get_db

automoviles = APIRouter()

@automoviles.get("/")
def root():
    return {"message":"Ruta default automovil"}

@automoviles.post("/automovil/create_automovil")
def create_automovil(data: AutomovilSchema, db: Session = Depends(get_db)):
    service = AutomovilService(db)
    return  service.create_automovil(data)

@automoviles.get("/automovil/get_all_automovil")
def get_all_automovil(db: Session = Depends(get_db)):
    service = AutomovilService(db)
    return  service.get_all_automovil()

@automoviles.get("/automovil/get_automovil/{apodo}")
def get_all_automovil(apodo:str, db: Session = Depends(get_db)):
    service = AutomovilService(db)
    return service.get_automovil(apodo)

@automoviles.put("/automovil/update_automovil/{id_automovil}")
def update_automovil(id_automovil: str, data: dict,db: Session = Depends(get_db)):
    service = AutomovilService(db)
    return  service.update_automovil(id_automovil, data)