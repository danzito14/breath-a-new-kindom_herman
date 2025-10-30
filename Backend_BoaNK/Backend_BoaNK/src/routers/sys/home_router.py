from fastapi import  APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.services.system.home_services.home_neededs import home_needs

home = APIRouter()

@home.get("/home/get_max_and_min_price", summary="Obtener el mminimo y el maximo para el sidebar")
def get_max_and_min_price(db: Session = Depends(get_db)):
    service = home_needs(db)
    return  service.get_min_and_max_price()