from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, select, update

from src.schemas.tipo_platillo_schema import Tipo_platilloSchema
from src.db.model.tipo_platillo_model import tipo_platillo
from src.core.db_credentials import get_db

class Tipo_platillosService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_tipo_platillo(self, data_tipo_platillo: Tipo_platilloSchema):
        tipo_platillo_dict = data_tipo_platillo.dict(exclude_unset=True)

        existe = self.db.execute(
            select(tipo_platillo).where(tipo_platillo.c.descripcion == tipo_platillo_dict["descripcion"])
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail=f"{tipo_platillo_dict['descripcion']} ya existe")

        stmt = insert(tipo_platillo).values(**tipo_platillo_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Tipo platillo agregado a favoritos"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_tipo_platillo(self):
        try:
            query = self.db.query(tipo_platillo).all()
            return  [dict(row._mapping) for row in query]
        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def update_tipo_platillo(self, id_tipo_platillo: int, data: dict):
        try:
            # Solo comprobar duplicados si se quiere actualizar la descripción
            if "descripcion" in data:
                existe = self.db.execute(
                    select(tipo_platillo)
                    .where(tipo_platillo.c.descripcion == data["descripcion"])
                    .where(tipo_platillo.c.id_tipo_platillo != id_tipo_platillo)
                    # importante: excluir el mismo registro
                ).first()

                if existe:
                    raise HTTPException(status_code=400, detail=f"{data['descripcion']} ya existe")

            # Ejecutar el update
            stmt = (
                update(tipo_platillo)
                .where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
                .values(**data)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se pudo actualizar los datos de Tipo platillo")

            return {"message": "Datos actualizados correctamente"}

        except HTTPException:
            raise  # volver a lanzar las HTTPException directamente
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_favorito(self, id_tipo_platillo: int):
        try:
            stmt = delete(tipo_platillo).where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró el Tipo favorito a eliminar")

            return {"message": "Tipo platillo eliminado correctamente"}  # ✅ respuesta útil
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


