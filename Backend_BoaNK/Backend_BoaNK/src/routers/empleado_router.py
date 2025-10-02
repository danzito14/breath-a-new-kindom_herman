import uuid
from src.schemas.empleados_schema import EmpleadosSchema
from src.db.model.empleado_model import empleado
from src.core.db_credentials import get_db
from fastapi import Body, APIRouter, Depends, HTTPException
from sqlalchemy.orm import  Session
from sqlalchemy import  insert, select, update, or_

from src.services.empelado_service import EmpleadoService
empleados = APIRouter()

@empleados.get("/empleado")
def root():
    return {"message":"Welcome Pilar de la Chamba"}

@empleados.post("/empleado/create_empleado")
def create_empleado(data_empleado: EmpleadosSchema, db: Session = Depends(get_db)):
    service = EmpleadoService(db)
    return service.create_empleado(data_empleado)

@empleados.get("/empleado/get_all_empleado")
def get_all_empleado(db:Session = Depends(get_db)):
    query = db.query(empleado).all()
    return [dict(row._mapping) for row in query]

@empleados.get("/empleado/get_empleado")
def get_empleado(
    Nombre: str = None,
    Apellido: str = None,
    db: Session = Depends(get_db)
):
    if not Nombre and not Apellido:
        raise HTTPException(status_code=400, detail="Debes proporcionar Nombre o Apellido.")

    condiciones = []
    if Nombre:
        condiciones.append(empleado.c.Nombre.like(f"%{Nombre}%"))
    if Apellido:
        condiciones.append(empleado.c.Apellido.like(f"%{Apellido}%"))

    stmt = select(empleado).where(or_(*condiciones))
    result = db.execute(stmt).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No se encontraron empleados.")

    #  Convertir cada fila en un dict legible
    empleados_list = [dict(row._mapping) for row in result]

    return {"total": len(empleados_list), "empleados": empleados_list}

@empleados.put("/empleado/update_empleado/{id_empleado}")
def update_empleado(id_empleado: str, data: dict = Body(...), db: Session = Depends(get_db)):
    stmt = (
        update(empleado).where(empleado.c.id_empleado == id_empleado).values(**data)
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="No se pudo actualizar los datos del empleado (ID no encontrado)"
        )

    return {"message": "Datos actualizados correctamente"}

