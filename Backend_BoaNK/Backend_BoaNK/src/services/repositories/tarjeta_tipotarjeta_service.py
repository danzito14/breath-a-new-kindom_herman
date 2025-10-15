import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, select, and_

from src.schemas.tarjeta_tipotarjeta_schema import Tarjetas_PagoSchema
from src.schemas.tarjeta_tipotarjeta_schema import Tipos_TarjetasSchema
from src.db.model.tarjeta_tipotarjetas_model import tarjetas_pago, tipos_tarjeta
from src.core.db_credentials import get_db


class Tarjetas_PagoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_tarjetas_pago(self, data_tarjetas_pago: Tarjetas_PagoSchema):
        tarjetas_pago_dict = data_tarjetas_pago.dict(exclude_unset=True)
        tarjetas_pago_dict["id_tarjeta"] = str(uuid.uuid4())  # ✅ Generar UUID

        # ✅ Extraer últimos 4 dígitos antes de guardar
        ultimos4 = tarjetas_pago_dict["num_tarjeta"][-4:]
        tarjetas_pago_dict["num_tarjeta"] = ultimos4

        # ✅ Verificar si ya existe una tarjeta con ese número para ese usuario
        existe = self.db.execute(
            select(tarjetas_pago).where(
            (tarjetas_pago.c.id_usuario == tarjetas_pago_dict["id_usuario"]) &
            (tarjetas_pago.c.num_tarjeta == ultimos4)
            )
        ).first()

        if existe:
            raise HTTPException(status_code=400, detail="Esta tarjeta ya está registrada para este usuario")

        stmt = insert(tarjetas_pago).values(**tarjetas_pago_dict)

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Tarjeta registrada correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_tarjetas_pago(self, id_usuario: str):
        try:
            stmt = select(tarjetas_pago).where(tarjetas_pago.c.id_usuario == id_usuario)
            result = self.db.execute(stmt)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_tarjeta_pago_by_titular(self, id_usuario: str, titular: str):
        try:
            stmt = select(tarjetas_pago).where(
                and_(
                    tarjetas_pago.c.id_usuario == id_usuario,
                    tarjetas_pago.c.titular.ilike(f"%{titular}%")
                )
            )
            result = self.db.execute(stmt)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


    def delete_tarjeta(self, id_tarjeta: str):
        try:
            stmt = delete(tarjetas_pago).where(tarjetas_pago.c.id_tarjeta == id_tarjeta)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se encontró la tarjeta a eliminar")

            return {"message": "Tarjeta eliminada correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

class Tipo_TarjetaService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_tipo_tarjetas(self, data_tipo_tarjeta: Tipos_TarjetasSchema):
        tipo_tarjetas_dict = data_tipo_tarjeta.dict(exclude_unset=True)

        # ✅ Verificar si ya existe una tarjeta con ese número para ese usuario
        existe = self.db.execute(
            select(tipos_tarjeta).where(
                (tipos_tarjeta.c.nombre == tipo_tarjetas_dict["nombre"]) &
                (tipos_tarjeta.c.categoria == tipo_tarjetas_dict["categoria"])
            )
        ).first()

        if existe:
            raise HTTPException(status_code=400, detail="Este tipo de tajeta ya esta registrada")

        stmt = insert(tipos_tarjeta).values(**tipo_tarjetas_dict)

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Tipo tarjeta registrada correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_tipo_tarjetas(self):
        try:
            stmt = select(tipos_tarjeta)
            result = self.db.execute(stmt)
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_tipo_tarjeta(self, id_tipo: int):
        try:
            stmt = delete(tipos_tarjeta).where(tipos_tarjeta.c.id_tipo_tarjeta == id_tipo)
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Tipo de tarjeta eliminado correctamente"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))