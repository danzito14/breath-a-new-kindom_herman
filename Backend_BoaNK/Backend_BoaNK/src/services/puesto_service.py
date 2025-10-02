from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update

from src.schemas.puesto_schema import PuestoSchema
from src.db.model.puesto_model import puesto
from src.core.db_credentials import get_db

class PuestoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_puesto(self, data_puesto: PuestoSchema):
        puesto_dict = data_puesto.dict(exclude_unset=True)

        stmt = insert(puesto).values(**puesto_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Puesto registrado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_puestos(self):
        try:
            query = self.db.query(puesto).all()  # ✅ corregido: antes consultaba empleado
            return [dict(row._mapping) for row in query]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_puesto(self, Nombre_puesto: str):
        spuesto = (
            self.db.query(puesto)
            .filter(puesto.c.Nombre_puesto == Nombre_puesto)
            .first()
        )
        if not spuesto:
            raise HTTPException(status_code=404, detail="Puesto no encontrado")
        return dict(spuesto._mapping)  # ✅ ahora sí retorna el resultado

    def update_puesto(self, id_puesto: int, data: dict):
        stmt = (
            update(puesto)
            .where(puesto.c.id_puesto == id_puesto)
            .values(**data)
        )
        result = self.db.execute(stmt)
        self.db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="No se pudo actualizar los datos del puesto (ID no encontrado)"
            )

        return {"message": "Datos actualizados correctamente"}
