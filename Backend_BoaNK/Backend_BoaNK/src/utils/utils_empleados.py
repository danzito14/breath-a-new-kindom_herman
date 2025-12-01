import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

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
                INSERT INTO codigo_validacion (id_usuario, codigo, correo_electronico)
                VALUES (:id, :codigo, :correo)
            """),
            {"id": current_user, "codigo": codigo_num, "correo": correo}
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
