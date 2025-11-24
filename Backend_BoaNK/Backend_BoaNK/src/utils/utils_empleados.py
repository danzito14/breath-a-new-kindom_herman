from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user
import random

from pydantic import BaseModel

class CorreoRequerido(BaseModel):
    correo: str

class CodigoRequerido(BaseModel):
    codigo:str

from src.services.system.email.email_service import EmailService

untils_empleados = APIRouter(prefix="/untils_empleados", tags=["Untils empleados"])

@untils_empleados.get("/get_nombre_empleado", summary="Buscar el rol y el nombre del chameador")
def get_vista_puesto_empledo(current_user: str = Depends(get_current_user), db: Session = Depends(get_db) ):
   try:
        """
            End point para buscar como se llaman nuestros cambeadores
        """
        stmt = text("SELECT * FROM vista_rol_empleado_usuario WHERE id_usuario = :id_usuario")
        resultado = db.execute(stmt, {"id_usuario": current_user}).mappings().first()

        if not resultado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

        return dict(resultado)

   except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.get("/get_nombre_nvl_usuario", summary="Buscar como se llama cada nvl de usuario")
def get_nombre_nvl_usuario(nvl_usuario: str, db:Session = Depends(get_db)):
    try:
        stmt = text("SELECT descripcion from nvl_usuario where id_nvl_usuario = :nvl_usuario")
        resultado = db.execute(stmt, {"nvl_usuario":nvl_usuario}).mappings().first()

        if not resultado:
            raise HTTPException(status_code=404, detail="nvl_usuario no encontrado")

        return dict(resultado)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.put("/generar_codigo", summary="Se generará un código para cambiar la contraseña")
def generar_codigo(
        data: CorreoRequerido,
        current_user: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        correo = data.correo
        codigo_num = random.randint(1000, 9999)

        # Eliminar código existente si ya hay uno para este usuario
        delete_stmt = text("""
            DELETE FROM codigo_validacion 
            WHERE id_usuario = :id_usuario
        """)

        db.execute(delete_stmt, {"id_usuario": current_user})
        db.commit()

        # Insertar nuevo código
        insert_stmt = text("""
            INSERT INTO codigo_validacion (id_usuario, codigo)
            VALUES (:id_usuario, :codigo)
        """)

        db.execute(insert_stmt, {
            "id_usuario": current_user,
            "codigo": codigo_num
        })

        db.commit()

        texto = f"Hola, el código para cambiar su contraseña es {codigo_num}"
        html = f"<h3>Hola, el código para cambiar su contraseña es:</h3><h1>{codigo_num}</h1>"

        EmailService().enviar_correo(
            destinatario=correo,
            asunto="Código para cambiar contraseña",
            texto=texto,
            html=html
        )

        return {"message": "Código enviado"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.post("/validar_codigo", summary="Validar código y cambiar contraseña")
def validar_codigo(
        data: CodigoRequerido,
        current_user: str = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    try:
        codigo = data.codigo

        # Validar el código
        select_stmt = text("""
            SELECT * FROM codigo_validacion
            WHERE id_usuario = :id_usuario AND codigo = :codigo
        """)

        result = db.execute(select_stmt, {
            "id_usuario": current_user,
            "codigo": codigo
        }).fetchone()

        if not result:
            return {"valid": False}

        # Si la validación es correcta, eliminar el código
        delete_stmt = text("""
            DELETE FROM codigo_validacion 
            WHERE id_usuario = :id_usuario
        """)

        db.execute(delete_stmt, {"id_usuario": current_user})
        db.commit()

        return {"valid": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))