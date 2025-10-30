from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, update, delete, select
from datetime import datetime

from src.db.model.activar_cuenta_model import activar_cuenta
from src.db.model.usuario_model import usuarios
from src.schemas.activar_cuenta_schema import Activar_CuentaSchema
from src.core.db_credentials import get_db


class activar_cuentaService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_codigo(self, **kwargs):
        required_fields = {"correo_electronico", "codigo", "create_at", "expira_at"}
        missing = required_fields - kwargs.keys()
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan los siguientes datos: {', '.join(missing)}"
            )

        try:
            cuenta = Activar_CuentaSchema(**kwargs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error en datos: {str(e)}")

        stmt = insert(activar_cuenta).values(**cuenta.dict())

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Código creado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def activar_cuenta(self, correo: str, codigo: str):
        try:
            verificacion = self.db.execute(
                select(activar_cuenta)
                .where(
                    (activar_cuenta.c.correo_electronico == correo)
                    & (activar_cuenta.c.codigo == codigo)
                )
            ).fetchone()

            if not verificacion:
                return {"exito": False, "mensaje": "Código o correo inválido."}

            # Verificar si el código expiró
            if verificacion.expira_at < datetime.utcnow():
                self.db.execute(
                    delete(activar_cuenta).where(activar_cuenta.c.correo_electronico == correo)
                )
                self.db.commit()
                return {"exito": False, "mensaje": "El código ha expirado."}

            # Activar al usuario
            self.db.execute(
                update(usuarios)
                .where(usuarios.c.Correo_electronico == correo)
                .values(estatus=True)
            )

            # Eliminar el código usado
            self.db.execute(
                delete(activar_cuenta)
                .where(activar_cuenta.c.correo_electronico == correo)
            )

            self.db.commit()
            return {"exito": True, "mensaje": "Cuenta activada correctamente."}

        except Exception as e:
            self.db.rollback()
            print(f"Error al activar cuenta: {str(e)}")
            return {"exito": False, "mensaje": "No se pudo activar la cuenta."}
