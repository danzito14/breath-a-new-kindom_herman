import os
import uuid
from pathlib import Path

from src.db.model.usuario_model import usuarios
from src.schemas.empleados_schema import EmpleadosSchema
from src.db.model.empleado_model import empleado
from src.core.db_credentials import get_db
from fastapi import Body, APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import  Session
from sqlalchemy import select, update, or_, func, text

from src.services.repositories.Cocineros_service import CocinerosService
from src.services.repositories.empelado_service import EmpleadoService
from src.services.repositories.repartidores_service import RepartidoresService

empleados = APIRouter(tags=["Empleado"])

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

@empleados.get("/empleado/get_empleado_by_id")
def get_all_empleado(id_empleado: str, db:Session = Depends(get_db)):
    query = db.query(empleado).where(empleado.c.id_empleado == id_empleado).first()
    return dict(query._mapping)

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
def update_empleado(id_empleado: str, data_emp: EmpleadosSchema, db: Session = Depends(get_db)):
    data = data_emp.dict(exclude_unset=True)
    # Obtener puesto anterior
    id_puesto_ant = db.execute(
        select(empleado.c.id_puesto).where(empleado.c.id_empleado == id_empleado)
    ).scalar()
    print("Puesto anterior:", id_puesto_ant)

    id_usuario = db.execute(
        select(empleado.c.id_usuario).where(empleado.c.id_empleado == id_empleado)
    ).scalar()

    if "estatus" in data:
        # actualizamos el estatus de la cuenta del empleado

        stmt_usu = (
            update(usuarios)
            .where(usuarios.c.id_usuario == id_usuario)
            .values(estatus=data["estatus"])
        )
        db.execute(stmt_usu)

    # --- Actualizar datos del empleado ---
    stmt = (
        update(empleado)
        .where(empleado.c.id_empleado == id_empleado)
        .values(**data)
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="No se pudo actualizar los datos del empleado (ID no encontrado)"
        )

    # Obtener nombre completo e ID usuario
    nombre_result = db.execute(
        select(func.concat(
            func.coalesce(empleado.c.Nombre, ''),
            ' ',
            func.coalesce(empleado.c.Apellido, '')
        )).where(empleado.c.id_empleado == id_empleado)
    ).scalar()


    if not nombre_result or nombre_result.strip() == "":
        nombre_result = None

    # ===============================================================
    # 1️⃣ LÓGICA PARA COCINEROS (Puesto 1)
    # ===============================================================
    if "id_puesto" in data and data["id_puesto"] == 1:

        service_cocinero = CocinerosService(db)
        try:
            service_cocinero.create_cocinero(
                id_usuario=id_usuario,
                nombre=nombre_result
            )
            print(f"👨‍🍳 Cocinero creado: {nombre_result}")
        except:
            print("⚠️ Cocinero ya existía, reactivando…")
            service_cocinero.update_cocinero(
                id_usuario=id_usuario,
                data={"estatus": True}
            )

    elif id_puesto_ant == 1:
        # Desactivar cocinero al cambiar de puesto
        try:
            service_cocinero = CocinerosService(db)
            service_cocinero.update_cocinero(
                id_usuario=id_usuario,
                data={"estatus": False}
            )
            print("🛑 Cocinero desactivado")
        except Exception as e:
            print(f"❌ Error desactivando cocinero: {e}")


    # ===============================================================
    # 2️⃣ LÓGICA PARA REPARTIDORES (Puesto 4)
    # ===============================================================
    if "id_puesto" in data and data["id_puesto"] == 4:

        service_repartidor = RepartidoresService(db)
        try:
            service_repartidor.create_repartidor(
                id_usuario=id_usuario,
                nombre=nombre_result
            )
            print(f"🚴‍♂️ Repartidor creado: {nombre_result}")
        except:
            print("⚠️ Repartidor ya existía, reactivando…")
            service_repartidor.update_repartidor(
                id_usuario=id_usuario,
                data={"estatus": True}
            )

    elif id_puesto_ant == 4:
        # Desactivar repartidor al cambiar de puesto
        try:
            service_repartidor = RepartidoresService(db)
            service_repartidor.update_repartidor(
                id_usuario=id_usuario,
                data={"estatus": False}
            )
            print("🛑 Repartidor desactivado")
        except Exception as e:
            print(f"❌ Error desactivando repartidor: {e}")


    return {
        "message": "Datos actualizados correctamente",
        "nombre": nombre_result
    }


@empleados.post("/empleado/actualizar_imagen_perfil")
async def actualizar_imagen_perfil(
        id_empleado: str = Form(...),  # Cambiar a Form en lugar de parámetro directo
        imagen: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        # Validar que sea imagen
        if not imagen.content_type.startswith("image/"):
            raise HTTPException(400, "El archivo debe ser una imagen")

        # Validar tamaño (5MB)
        contents = await imagen.read()
        if len(contents) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(400, "La imagen no debe superar los 5MB")

        # Resetear el puntero del archivo
        await imagen.seek(0)

        # Crear carpeta si no existe
        upload_dir = Path("public/empleados/profiles")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generar nombre único
        ext = os.path.splitext(imagen.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = upload_dir / filename

        # Guardar imagen
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        ruta_imagen = f"/public/empleados/profiles/{filename}"

        # Actualizar BD
        stmt = text("""
            UPDATE empleado
            SET Ruta_imagen = :ruta_imagen 
            WHERE id_empleado = :id_empleado
        """)

        result = db.execute(stmt, {
            "ruta_imagen": ruta_imagen,
            "id_empleado": id_empleado
        })

        # Verificar si se actualizó algún registro
        if result.rowcount == 0:
            # Eliminar la imagen recién subida si no se encontró el empleado
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(404, "Empleado no encontrado")

        db.commit()

        return {
            "message": "Imagen actualizada correctamente",
            "ruta": ruta_imagen,
            "id_empleado": id_empleado
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error en actualizar_imagen_perfil: {str(e)}")
        raise HTTPException(500, f"Error al procesar la imagen: {str(e)}")

        db.execute(stmt, {
            "ruta_imagen": ruta_imagen,
            "id_empleado": id_empleado
        })
        db.commit()

        return {
            "message": "Imagen actualizada correctamente",
            "ruta": ruta_imagen
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))

