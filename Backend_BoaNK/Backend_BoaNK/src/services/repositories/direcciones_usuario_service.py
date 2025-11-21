import uuid
from fastapi import Depends, HTTPException
from pyDatalog.examples.python import result
from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, select, and_, update

from src.schemas.direcciones_usuario_schema import Direcciones_usuarioSchema
from src.db.model.direcciones_usuario_model import direcciones_usuario
from src.core.db_credentials import get_db

class Direcciones_usuarioService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_direcciones_usuario(self, data_direccion_usuario: Direcciones_usuarioSchema):
        direccion_usuario_dict = data_direccion_usuario.dict(exclude_unset=True)
        direccion_usuario_dict["id_direccion"] = str(uuid.uuid4())  # ✅ generar antes del insert

        existe = self.db.execute(
            select(direcciones_usuario).where(
                (direcciones_usuario.c.alias == direccion_usuario_dict['alias']) &
                (direcciones_usuario.c.id_usuario == direccion_usuario_dict['id_usuario'])
            )
        ).first()

        if existe:
            raise HTTPException(status_code=400, detail=f"El alias {direccion_usuario_dict['alias']} ya existe")

        stmt = insert(direcciones_usuario).values(**direccion_usuario_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Direccion agregado", "id_direccion": direccion_usuario_dict["id_direccion"]}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_direcciones_usuario(self, id_usuario: str):
        try:
            stmt = select(direcciones_usuario).where(direcciones_usuario.c.id_usuario == id_usuario)
            result = self.db.execute(stmt).all()
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_direccion_usuario(self, id_usuario: str, alias: str):
        try:
            stmt = select(direcciones_usuario).where(
                and_(
                    direcciones_usuario.c.alias.ilike(f"%{alias}%"),
                    direcciones_usuario.c.id_usuario == id_usuario
                )
            )
            result = self.db.execute(stmt).all()
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_direccion_usuario(self, id_direccion: str, data: dict):
        try:
            if "alias" in data:
                existe = self.db.execute(
                    select(direcciones_usuario).where(
                        and_(
                            direcciones_usuario.c.alias == data['alias'],
                            direcciones_usuario.c.id_direccion != id_direccion
                        )
                    )
                ).first()

                if existe:
                    raise HTTPException(status_code=400, detail=f"El alia {data['alias']} ya existe")

            stmt = (
                update(direcciones_usuario)
                .where(direcciones_usuario.c.id_direccion == id_direccion)
                .values(**data)
            )
            result = self.db.execute(stmt)
            self.db.commit()  # ✅ MUY IMPORTANTE

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró la dirección")

            return {"message": "Dirección actualizada correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete_direcciones_usuario(self, id_direccion: str):
        try:
            stmt = delete(direcciones_usuario).where(direcciones_usuario.c.id_direccion == id_direccion)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró el direcciones_usuario a eliminar")

            return {"message": "Direccion eliminada correctamente"}  # ✅ respuesta útil
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
