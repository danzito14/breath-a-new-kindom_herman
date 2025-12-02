import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from passlib.context import CryptContext

from sqlalchemy import text, select, and_, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user, func

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
import random

from pydantic import BaseModel

from src.db.model.cocineros_model import cocina
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.pedidos.repartidores_model import repartidores
from src.db.model.usuario_model import usuarios



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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

@untils_empleados.put("/generar_codigo", summary="Generar código para cambiar contraseña")
def generar_codigo(
    data: CorreoRequerido,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        correo = data.correo
        codigo_num = secrets.randbelow(9000) + 1000  # código seguro de 4 dígitos

        # Eliminar código anterior
        db.execute(
            text("DELETE FROM codigo_validacion WHERE id_usuario = :id"),
            {"id": current_user}
        )

        # Insertar nuevo código
        db.execute(
            text("""
                INSERT INTO codigo_validacion (id_usuario, codigo)
                VALUES (:id, :codigo)
            """),
            {"id": current_user, "codigo": codigo_num}
        )

        db.commit()

        texto = f"Hola, tu código para cambiar la contraseña es {codigo_num}"
        html = f"<h3>Hola</h3><p>Tu código para cambiar la contraseña es:</p><h1>{codigo_num}</h1>"

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





@untils_empleados.put("/cambio_correo", summary="Solicitar cambio de correo electrónico")
def cambiar_correo(
    nickname: str,
    data: CorreoRequerido,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        correo = data.correo

        # Validar si ya existe un cambio pendiente
        result = db.execute(
            text("""
                SELECT * FROM cambio_correo
                WHERE id_usuario = :id
            """),
            {"id": current_user}
        ).first()

        if result:
            raise HTTPException(
                status_code=400,
                detail="Ya existe un cambio de correo pendiente. Primero confirma ese cambio."
            )

        # Registrar cambio de correo
        db.execute(
            text("""
                INSERT INTO cambio_correo (id_usuario, correo_electronico)
                VALUES (:id, :correo)
            """),
            {"id": current_user, "correo": correo}
        )

        db.commit()

        url_validacion = (
            f"https://breath-a-new-kindomherman-production.up.railway.app/"
            f"untils_empleados/validar_cambio_correo?correo={correo}&id_usuario={current_user}"
        )

        html = f"""
        <html>
        <body>
            <h2>Hola {nickname},</h2>
            <p>Hemos detectado que deseas cambiar tu correo electrónico.</p>
            <p>Haz clic en el siguiente botón para confirmar el cambio:</p>
            <a href="{url_validacion}" style="
                background-color: #D0AF43;
                padding: 12px 20px;
                border-radius: 10px;
                color: white;
                text-decoration: none;
                font-size: 18px;
            ">Confirmar Cambio</a>
        </body>
        </html>
        """

        EmailService().enviar_correo(
            destinatario=correo,
            asunto="Confirmación de cambio de correo",
            texto="Confirma el cambio de correo electrónico",
            html=html
        )

        return {"message": "Correo de confirmación enviado"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@untils_empleados.post("/validar_codigo", summary="Validar código enviado por correo")
def validar_codigo(
    data: CodigoRequerido,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        codigo = data.codigo

        result = db.execute(
            text("""
                SELECT * FROM codigo_validacion
                WHERE id_usuario = :id AND codigo = :codigo
            """),
            {"id": current_user, "codigo": codigo}
        ).fetchone()

        if not result:
            return {"valid": False}

        # Si es válido, eliminamos el código
        db.execute(
            text("DELETE FROM codigo_validacion WHERE id_usuario = :id"),
            {"id": current_user}
        )
        db.commit()

        return {"valid": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@untils_empleados.get("/validar_cambio_correo", summary="Validar cambio de correo")
def validar_cambio_correo(
    correo: str,
    id_usuario: str,
    db: Session = Depends(get_db)
):
    try:
        # Verificar que exista solicitud pendiente
        result = db.execute(
            text("""
                SELECT * FROM cambio_correo
                WHERE id_usuario = :id AND correo_electronico = :correo
            """),
            {"id": id_usuario, "correo": correo}
        ).fetchone()

        if not result:
            return RedirectResponse(
                url="https://restaurantbreathofanewkindom.up.railway.app/auth-error"
            )

        # Actualizar correo en tabla usuarios
        db.execute(
            text("""
                UPDATE usuarios
                SET Correo_electronico = :correo
                WHERE id_usuario = :id
            """),
            {"correo": correo, "id": id_usuario}
        )

        # Eliminar registro temporal
        db.execute(
            text("DELETE FROM cambio_correo WHERE id_usuario = :id"),
            {"id": id_usuario}
        )

        db.commit()

        return RedirectResponse(
            url="https://restaurantbreathofanewkindom.up.railway.app"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.get("/logout_mesero", summary=" Se verificara si todos los pedidos ya estan servidos y/o pagados que sean para mesa")
def logout_mesero(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    hoy = datetime.now().date()

    estados_pedido_activos = ['Pendiente', 'Preparando', 'Listo', 'En camino', 'Entregado']
    estados_detalle_activos = ['pendiente', 'cocinando', 'listo']

    query = (
        select(func.count())
        .select_from(pedido.join(detalle_pedido, pedido.c.id_pedido == detalle_pedido.c.id_pedido))
        .where(
            and_(
                pedido.c.Tipo_pedido == 'Local',
                pedido.c.Estado.in_(estados_pedido_activos),
                detalle_pedido.c.estado.in_(estados_detalle_activos),
                func.date(pedido.c.Fecha) == hoy
            )
        )
    )

    result = db.execute(query)
    (total,) = result.fetchone()

    return total == 0  # Si no hay pedidos activos → puede salir

@untils_empleados.get("/logout_repartidor")
def logout_repartidor(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    hoy = datetime.now().date()

    estados_pedido_activos = ['Pendiente', 'Preparando', 'Listo', 'En camino', 'Entregado']
    estados_detalle_activos = ['pendiente', 'cocinando', 'listo']

    query = (
        select(func.count())
        .select_from(pedido.join(detalle_pedido, pedido.c.id_pedido == detalle_pedido.c.id_pedido))
        .where(
            and_(
                pedido.c.Tipo_pedido == 'Entrega',
                pedido.c.Estado.in_(estados_pedido_activos),
                detalle_pedido.c.estado.in_(estados_detalle_activos),
                func.date(pedido.c.Fecha) == hoy
            )
        )
    )

    result = db.execute(query)
    (total,) = result.fetchone()

    if total == 0:
        # Marcar repartidor como inactivo
        db.execute(
            update(repartidores).values(activo=False).where(repartidores.c.id_usuario == current_user)
        )
        db.commit()
        return True

    return False



@untils_empleados.get("/logout_cocinero")
def logout_cocinero(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    hoy = datetime.now().date()

    estados_detalle_activos = ['pendiente', 'cocinando', 'listo']

    query = (
        select(func.count())
        .select_from(detalle_pedido.join(pedido, pedido.c.id_pedido == detalle_pedido.c.id_pedido))
        .where(
            and_(
                func.date(pedido.c.Fecha) == hoy,
                detalle_pedido.c.estado.in_(estados_detalle_activos)
            )
        )
    )

    result = db.execute(query)
    (total,) = result.fetchone()

    if total == 0:
        # Marcar cocinero como inactivo
        db.execute(
            update(cocina).values(estatus=False).where(cocina.c.id_usuario == current_user)
        )
        db.commit()
        return True

    return False

@untils_empleados.get("/recuperar_contra")
def recuperar_contra(nickname:str, db:Session = Depends(get_db)):
    #Vemos si existe un correo para ese usuario

    correo = db.execute(
        select(usuarios.c.Correo_electronico).where(usuarios.c.Nickname == nickname)).scalar()

    if not correo:
        raise HTTPException(status_code=400, detail="No se ha encontrado ningun correo asociado a este nickname")
    else:
        return  {"correo": correo}


# Agregar estos modelos Pydantic al inicio del archivo
class CorreoCodigoRequerido(BaseModel):
    correo: str
    codigo: str


class CambioContrasenaPublico(BaseModel):
    correo: str
    codigo: str
    nueva_contrasena: str


# ========== ENDPOINTS PÚBLICOS PARA RECUPERACIÓN DE CONTRASEÑA ==========

@untils_empleados.put("/generar_codigo_publico", summary="Generar código para cambiar contraseña (PÚBLICO)")
def generar_codigo_publico(
        data: CorreoRequerido,
        db: Session = Depends(get_db)
):
    """
    Endpoint PÚBLICO (sin autenticación) para enviar código de recuperación.
    Este endpoint NO requiere token de autenticación.
    """
    try:
        correo = data.correo

        # Buscar usuario por correo
        usuario = db.execute(
            select(usuarios.c.id_usuario).where(usuarios.c.Correo_electronico == correo)
        ).scalar()

        if not usuario:
            raise HTTPException(status_code=404, detail="No existe un usuario con ese correo")

        # Generar código de 4 dígitos de forma segura
        codigo_num = secrets.randbelow(9000) + 1000

        # Eliminar código anterior si existe
        db.execute(
            text("DELETE FROM codigo_validacion WHERE id_usuario = :id"),
            {"id": usuario}
        )

        # Insertar nuevo código con timestamp
        db.execute(
            text("""
                INSERT INTO codigo_validacion (id_usuario, codigo)
                VALUES (:id, :codigo)
            """),
            {"id": usuario, "codigo": codigo_num}
        )

        db.commit()

        # Enviar correo con diseño profesional
        texto = f"Hola, tu código para recuperar tu contraseña es {codigo_num}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #D0AF43; text-align: center;">Recuperación de Contraseña</h2>
                <p>Hola,</p>
                <p>Has solicitado recuperar tu contraseña. Tu código de verificación es:</p>
                <div style="background-color: #f5f5f5; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0; border: 2px solid #D0AF43;">
                    <h1 style="color: #773832; font-size: 48px; margin: 0; letter-spacing: 10px;">{codigo_num}</h1>
                </div>
                <p style="color: #666; font-size: 14px;">⏰ Este código expirará en 15 minutos.</p>
                <p style="color: #666; font-size: 14px;">⚠️ Si no solicitaste este código, ignora este mensaje.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #877129; text-align: center;">Saludos,<br><strong>Breath of a New Kingdom</strong></p>
            </div>
        </body>
        </html>
        """

        EmailService().enviar_correo(
            destinatario=correo,
            asunto="Código de Recuperación de Contraseña",
            texto=texto,
            html=html
        )

        return {"message": "Código enviado correctamente", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.post("/validar_codigo_publico", summary="Validar código de recuperación (PÚBLICO)")
def validar_codigo_publico(
        data: CorreoCodigoRequerido,
        db: Session = Depends(get_db)
):
    """
    Endpoint PÚBLICO (sin autenticación) para validar el código de 4 dígitos.
    Verifica que el código sea correcto y no haya expirado (15 minutos).
    """
    try:
        correo = data.correo
        codigo = data.codigo

        # Buscar usuario por correo
        usuario = db.execute(
            select(usuarios.c.id_usuario).where(usuarios.c.Correo_electronico == correo)
        ).scalar()

        if not usuario:
            return {"valid": False, "message": "Usuario no encontrado"}

        # Validar código (considera expiración de 15 minutos)
        result = db.execute(
            text("""
                SELECT * FROM codigo_validacion
                WHERE id_usuario = :id 
                AND codigo = :codigo
            """),
            {"id": usuario, "codigo": codigo}
        ).fetchone()

        if not result:
            return {"valid": False, "message": "Código incorrecto o expirado"}

        # NO eliminamos el código aquí, lo haremos después de cambiar la contraseña
        return {"valid": True, "message": "Código válido"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@untils_empleados.put("/cambiar_contrasena_publico", summary="Cambiar contraseña con código (PÚBLICO)")
def cambiar_contrasena_publico(
        data: CambioContrasenaPublico,
        db: Session = Depends(get_db)
):
    """
    Endpoint PÚBLICO (sin autenticación) para cambiar la contraseña usando el código.
    Valida el código nuevamente por seguridad y hashea la nueva contraseña.
    """
    try:
        correo = data.correo
        codigo = data.codigo
        nueva_contrasena = data.nueva_contrasena

        # Validar que la contraseña tenga al menos 6 caracteres
        if len(nueva_contrasena) < 6:
            raise HTTPException(
                status_code=400,
                detail="La contraseña debe tener al menos 6 caracteres"
            )

        # Buscar usuario por correo
        usuario = db.execute(
            select(usuarios.c.id_usuario).where(usuarios.c.Correo_electronico == correo)
        ).scalar()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Validar código nuevamente por seguridad
        result = db.execute(
            text("""
                SELECT * FROM codigo_validacion
                WHERE id_usuario = :id 
                AND codigo = :codigo
            """),
            {"id": usuario, "codigo": codigo}
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=400,
                detail="Código incorrecto o expirado"
            )

        # Hashear la nueva contraseña usando el mismo pwd_context que update_user
        nueva_contrasena_hash = pwd_context.hash(nueva_contrasena)

        # Actualizar contraseña con hash (MySQL usa backticks)
        db.execute(
            text("""
                UPDATE usuarios
                SET `Contraseña` = :contrasena
                WHERE id_usuario = :id
            """),
            {"contrasena": nueva_contrasena_hash, "id": usuario}
        )

        # Eliminar el código usado (seguridad: código de un solo uso)
        db.execute(
            text("DELETE FROM codigo_validacion WHERE id_usuario = :id"),
            {"id": usuario}
        )

        db.commit()

        # Enviar correo de confirmación
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #D0AF43; text-align: center;">✅ Contraseña Actualizada</h2>
                <p>Tu contraseña ha sido cambiada exitosamente.</p>
                <p style="color: #666;">Ya puedes iniciar sesión con tu nueva contraseña.</p>
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #D0AF43; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;"><strong>⚠️ Importante:</strong> Si no realizaste este cambio, contacta inmediatamente con soporte.</p>
                </div>
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #877129; text-align: center;">Saludos,<br><strong>Breath of a New Kingdom</strong></p>
            </div>
        </body>
        </html>
        """

        EmailService().enviar_correo(
            destinatario=correo,
            asunto="Contraseña Actualizada - Breath of a New Kingdom",
            texto="Tu contraseña ha sido cambiada exitosamente",
            html=html
        )

        return {"message": "Contraseña actualizada correctamente", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))