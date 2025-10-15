import uuid

from src.schemas.platillos_schema import PlatilloSchema
from src.db.model.platillo_model import platillo
from src.core.db_credentials import get_db
from fastapi import Body, APIRouter, Depends, HTTPException
from sqlalchemy.orm import  Session
from sqlalchemy import  insert, select, update

platillos = APIRouter()

@platillos.get("/platillo")
def root():
    return {"mesage":"Welcome to Breath of a New Kingdom"}

@platillos.post("/platillo/create_platillo")
def create_platillo(data_platillo: PlatilloSchema, db: Session = Depends(get_db)):

    #Generar el id
    platillo_dict = data_platillo.dict(exclude_unset=True)
    platillo_dict ["id_platillo"] = str(uuid.uuid4())

    #Generamos el stmt
    stmt = insert(platillo).values(**platillo_dict)
    try:
        db.execute(stmt)
        db.commit()
        return {"message":"Platillo creado correctamente", "nombre": platillo_dict["Nombre_platillo"]}
    except Exception as e:
        db.roolback()
        raise  HTTPException(status_code=400, detail=str(e))

@platillos.get("/platillo/get_all_platillos")
def get_all_platillos(db:Session = Depends(get_db)):
    query = db.query(platillo).all()
    return [dict(row._mapping) for row in query]

@platillos.get("/platillo/get_platillo")
def get_platillo(Nombre_platillo: str, db: Session = Depends(get_db)):
    stmt = select(platillo).where(platillo.c.Nombre_platillo == Nombre_platillo)
    plato = db.execute(stmt).first()

    if not plato:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return dict(plato._mapping)

@platillos.put("/platillo/update_platillo/{id}")
def update_platillo(id_platillo: str, data: dict = Body(...), db: Session = Depends(get_db)):
    stmt = (
        update(platillo)
        .where(platillo.c.id_platillo == id_platillo)
        .values(**data)
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"message": "Platillo actualizado correctamente"}


