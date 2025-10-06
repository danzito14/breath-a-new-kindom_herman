from fastapi import Body, APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.uniforme_schema import UniformeSchema
from src.services.uniforme_service import UniformeService
from src.core.db_credentials import get_db

uniformes = APIRouter()


@uniformes.get("/")
def root():
    return {"message":"Ruta default uniforme"}

@uniformes.post("/uniforme/create_uniforme")
def create_uniforme(data: UniformeSchema, db: Session = Depends(get_db)):
    service = UniformeService(db)
    return  service.create_uniforme(data)

@uniformes.get("/uniforme/get_all_uniforme")
def get_all_uniforme(db: Session = Depends(get_db)):
    service = UniformeService(db)
    return  service.get_all_uniforme()

@uniformes.get("/uniforme/get_uniforme/{Descripcion}")
def get_all_uniforme(Descripcion:str, db: Session = Depends(get_db)):
    service = UniformeService(db)
    return service.get_uniforme(Descripcion)

@uniformes.put("/uniforme/update_uniforme/{id_uniforme}")
def update_uniforme(id_uniforme: str, data: dict,db: Session = Depends(get_db)):
    service = UniformeService(db)
    return  service.update_uniforme(id_uniforme, data)