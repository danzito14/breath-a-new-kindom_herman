import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert,select, update, and_

from src.db.model.uniforme_model import uniforme
from src.schemas.uniforme_schema import UniformeSchema
from src.core.db_credentials import get_db

class UniformeService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_uniforme(self, data_uniforme: UniformeSchema):
        uniforme_dict = data_uniforme.dict(exclude_unset=True)
        existe = self.db.execute(
            select(uniforme).where(
                and_(
                    uniforme.c.id_puesto == uniforme_dict['id_puesto'],
                    uniforme.c.Talla == uniforme_dict['Talla'],
                    uniforme.c.Descripcion == uniforme_dict['Descripcion'],

                )
            )
        ).first()

        if existe:
            raise HTTPException(status_code=400, detail=f"El uniforme ya existe")

        stmt = insert(uniforme).values(**uniforme_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": f"El uniforme ha sido agregado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_uniforme(self):
        try:
            query = self.db.query(uniforme).all()
            return  [dict(row._mapping) for row in query]
        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def get_uniforme(self, id_uniforme: int):
        try:
            stmt = select(uniforme).where(uniforme.c.id_uniforme == id_uniforme)
            result = self.db.execute(stmt).first()

            if not result:
                raise HTTPException(status_code=400, detail="Uniforme no encontrado")

            return dict(result._mapping)

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_uniforme (self, id_uniforme:int, data:dict):
        try:

            if "Talla" in data and "Descripcion" in data and "id_puesto" in data:
                existe = self.db.execute(
                    select(uniforme).where(
                        and_(
                            uniforme.c.id_puesto == data['id_puesto'],
                            uniforme.c.Talla == data['Talla'],
                            uniforme.c.Descripcion == data['Descripcion'],
                            uniforme.c.id_uniforme != id_uniforme
                        )
                    )
                ).first()

                if existe:
                    raise  HTTPException(status_code=400, detail=f" ya existe")

            stmt = (update(uniforme).where(uniforme.c.id_uniforme == id_uniforme).values(**data))

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se pudo actualizar los datos de uniforme")

            return {"message": "Datos actualizados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
