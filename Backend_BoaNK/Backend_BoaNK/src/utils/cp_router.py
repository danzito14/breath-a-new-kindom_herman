from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.model.CP_model import cp
from src.core.db_credentials import get_db

utils = APIRouter(prefix="/utils", tags=["Utils"])


@utils.get("/buscar_cp", summary="Buscar el código postal")
def buscar_cp(codigo: int, db: Session = Depends(get_db)):
    resultados = db.query(cp).filter(cp.c.codigo == codigo).all()
    if not resultados:
        raise HTTPException(status_code=404, detail="Código postal no encontrado")

    return [dict(row._mapping) for row in resultados]