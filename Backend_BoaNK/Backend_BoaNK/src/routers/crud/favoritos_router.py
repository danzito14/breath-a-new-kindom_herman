from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.schemas.favoritos_schema import FavoritosSchema
from src.services.repositories.favoritos_service import FavoritosService
from src.core.db_credentials import get_db

favorito = APIRouter()

@favorito.get("/")
def root():
    return {"message":"Ruta de platillos favoritos"}

@favorito.post("/favoritos/create_favorito", summary="Agregar un platillo a favoritos")
def create_favoritos(data:FavoritosSchema, db: Session = Depends(get_db)):
    service = FavoritosService(db)
    return  service.create_favorito(data)

@favorito.get("/favoritos/get_all_favoritos/{id_usuario}")
def get_all_favoritos(id_usuario: str, db: Session = Depends(get_db)):
    service = FavoritosService(db)
    return  service.get_all_favoritos(id_usuario)

@favorito.delete("/favoritos/delete_favorito/{id_favorito}", summary="Eliminar un platillo de favoritos")
def delete_favorito(id_favorito: str, db: Session = Depends(get_db)):
    service = FavoritosService(db)
    return service.delete_favorito(id_favorito)