import uuid
import os
from datetime import datetime
from pathlib import Path

from src.schemas.platillos_schema import PlatilloSchema, OpcionplatilloSchema
from src.db.model.platillo_model import platillo, opcion_platillo
from src.db.model.tipo_platillo_model import tipo_platillo
from src.db.model.ofertas_model import ofertas, oferta_platillos
from src.core.db_credentials import get_db
from fastapi import Body, APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, delete, func, and_
import shutil

platillos = APIRouter(tags=["Platillos"])

# Configuración de directorio para imágenes
UPLOAD_DIR = Path("public/productos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file: UploadFile) -> None:
    """Valida que el archivo sea una imagen válida"""
    # Validar extensión
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido. Use: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validar tipo MIME
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser una imagen"
        )


def generate_unique_filename(original_filename: str) -> str:
    """Genera un nombre único para el archivo"""
    file_ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{file_ext}"
    return unique_name


@platillos.post("/platillo/upload_image", summary="Subir imagen de platillo")
async def upload_platillo_image(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Sube una imagen para un platillo al servidor.
    Retorna la ruta donde se guardó la imagen.
    """
    try:
        # Validar archivo
        validate_image_file(file)

        # Validar tamaño
        file.file.seek(0, 2)  # Ir al final del archivo
        file_size = file.file.tell()  # Obtener tamaño
        file.file.seek(0)  # Volver al inicio

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo es demasiado grande. Máximo: {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )

        # Generar nombre único
        filename = generate_unique_filename(file.filename)
        file_path = UPLOAD_DIR / filename

        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Retornar ruta relativa
        relative_path = f"public/productos/{filename}"

        return {
            "message": "Imagen subida exitosamente",
            "filename": filename,
            "ruta_imagen": relative_path,
            "url": f"/platillo/image/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")
    finally:
        file.file.close()


@platillos.get("/platillo/image/{filename}", summary="Obtener imagen de platillo")
async def get_platillo_image(filename: str):
    """
    Sirve una imagen de platillo
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    return FileResponse(file_path)


@platillos.delete("/platillo/delete_image/{filename}", summary="Eliminar imagen de platillo")
async def delete_platillo_image(filename: str, db: Session = Depends(get_db)):
    """
    Elimina una imagen de platillo del servidor
    """
    try:
        file_path = UPLOAD_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Imagen no encontrada")

        # Eliminar archivo
        os.remove(file_path)

        return {
            "message": "Imagen eliminada exitosamente",
            "filename": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar imagen: {str(e)}")


@platillos.put("/platillo/update_image/{id_platillo}", summary="Actualizar imagen de platillo")
async def update_platillo_image(
        id_platillo: str,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Actualiza la imagen de un platillo existente.
    Elimina la imagen anterior si existe.
    """
    try:
        # Validar que el platillo existe
        stmt = select(platillo).where(platillo.c.id_platillo == id_platillo)
        platillo_actual = db.execute(stmt).fetchone()

        if not platillo_actual:
            raise HTTPException(status_code=404, detail="Platillo no encontrado")

        # Validar archivo
        validate_image_file(file)

        # Validar tamaño
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo es demasiado grande. Máximo: {MAX_FILE_SIZE / (1024 * 1024)}MB"
            )

        # Eliminar imagen anterior si existe
        if platillo_actual.Ruta_imagen:
            old_filename = Path(platillo_actual.Ruta_imagen).name
            old_file_path = UPLOAD_DIR / old_filename
            if old_file_path.exists():
                os.remove(old_file_path)

        # Generar nombre único para nueva imagen
        filename = generate_unique_filename(file.filename)
        file_path = UPLOAD_DIR / filename

        # Guardar nuevo archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Actualizar ruta en la base de datos
        relative_path = f"public/productos/{filename}"
        stmt_update = (
            update(platillo)
            .where(platillo.c.id_platillo == id_platillo)
            .values(Ruta_imagen=relative_path)
        )
        db.execute(stmt_update)
        db.commit()

        return {
            "message": "Imagen actualizada exitosamente",
            "filename": filename,
            "ruta_imagen": relative_path,
            "url": f"/platillo/image/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar imagen: {str(e)}")
    finally:
        file.file.close()


@platillos.get("/platillo")
def root():
    return {"mesage": "Welcome to Breath of a New Kingdom"}


@platillos.post("/platillo/create_platillo")
def create_platillo(data_platillo: PlatilloSchema, db: Session = Depends(get_db)):
    # Generar el id
    platillo_dict = data_platillo.dict(exclude_unset=True)
    platillo_dict["id_platillo"] = str(uuid.uuid4())

    # Generamos el stmt
    stmt = insert(platillo).values(**platillo_dict)
    try:
        db.execute(stmt)
        db.commit()
        return {
            "message": "Platillo creado correctamente",
            "nombre": platillo_dict["Nombre_platillo"],
            "id_platillo": platillo_dict["id_platillo"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@platillos.post("/platillo/create_options_platillo", summary="Darle opciones de personalizacion a un platillo")
def create_option_platillo(data_option: OpcionplatilloSchema, db: Session = Depends(get_db)):
    try:
        data_dict = data_option.dict(exclude_unset=True)

        stmt = select(opcion_platillo).where(
            (opcion_platillo.c.opcion == data_dict["opcion"]) &
            (opcion_platillo.c.id_platillo == data_dict["id_platillo"])
        )

        existe_option = db.execute(stmt).fetchone()

        if existe_option:
            raise HTTPException(status_code=400, detail="Opcion de plato existente")

        stmt = insert(opcion_platillo).values(**data_dict)
        try:
            db.execute(stmt)
            db.commit()
            return {"message": "Opcion de personalizacion de plato agregada correctamente",
                    "nombre": data_dict["opcion"]}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@platillos.get("/platillos/get_platillo_option", summary="Obtener las opciones de un platillo")
def get_option_platillo(id_platillo: str, db: Session = Depends(get_db)):
    stmt = db.query(opcion_platillo).where(opcion_platillo.c.id_platillo == id_platillo).all()
    return [dict(row._mapping) for row in stmt]


@platillos.get("/platillo/get_all_platillos")
def get_all_platillos(db: Session = Depends(get_db)):
    # Obtener todos los platillos
    query = db.query(platillo).all()
    platillos_lista = []

    for row in query:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo")
def get_platillo(Nombre_platillo: str, db: Session = Depends(get_db)):
    stmt = select(platillo).where(platillo.c.Nombre_platillo.ilike(f"%{Nombre_platillo}%"))
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo_id_adm")
def get_platillo_by_id(id: str, db: Session = Depends(get_db)):
    stmt = (
        select(platillo).where(platillo.c.id_platillo == id)
    )
    plato = db.execute(stmt).first()

    return dict(plato._mapping)


@platillos.get("/platillo/get_platillo_id")
def get_platillo_by_id(id: str, db: Session = Depends(get_db)):
    stmt = (
        select(
            platillo.c.id_platillo,
            platillo.c.Nombre_platillo,
            platillo.c.Ruta_imagen,
            platillo.c.precio_venta,
            platillo.c.Descripcion,
            tipo_platillo.c.descripcion,
            tipo_platillo.c.color
        )
        .select_from(platillo.join(tipo_platillo, platillo.c.id_tipo_platillo == tipo_platillo.c.id_tipo_platillo))
        .where(platillo.c.id_platillo == id)
    )
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo_by_tipo", summary="Obtener los platillos por categoria")
def get_platillo_by_tipo(id_tipo_platillo: int, db: Session = Depends(get_db)):
    stmt = select(platillo).where(platillo.c.id_tipo_platillo == id_tipo_platillo)
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo_by_price", summary="Obtener por precio")
def get_platillo_by_price(min_price: int, max_price: int, db: Session = Depends(get_db)):
    stmt = select(platillo).where(
        (platillo.c.precio_venta >= min_price) & (platillo.c.precio_venta <= max_price)
    )
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.put("/platillo/update_platillo")
def update_platillo(
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    id_platillo = payload["id"]
    data = payload["platillo"]

    stmt = (
        update(platillo)
        .where(platillo.c.id_platillo == id_platillo)
        .values(**data)
    )

    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")

    return {"message": "Platillo actualizado correctamente"}


@platillos.put("/platillo/update_options_platillo", summary="Actualizar una opción de personalización de un platillo")
def update_option_platillo(id_option: str, data_option: dict = Body(...), db: Session = Depends(get_db)):
    try:
        if "opcion" in data_option:
            stmt_check = select(opcion_platillo).where(
                (opcion_platillo.c.opcion == data_option["opcion"]) &
                (opcion_platillo.c.id_platillo == data_option["id_platillo"]) &
                (opcion_platillo.c.id_option != id_option)
            )

            existe_option = db.execute(stmt_check).fetchone()

            if existe_option:
                raise HTTPException(status_code=400, detail="Ya existe una opción con ese nombre para este platillo")

        stmt_update = (
            update(opcion_platillo)
            .where(opcion_platillo.c.id_option == id_option)
            .values(**data_option)
        )

        result = db.execute(stmt_update)
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="No se encontró la opción especificada")

        return {
            "message": "Opción de personalización actualizada correctamente",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@platillos.delete("/platillo/delete_option/{id_option}",
                  summary="Eliminar una opción de personalización de un platillo")
def delete_option_platillo(id_option: str, db: Session = Depends(get_db)):
    try:
        stmt_check = select(opcion_platillo).where(opcion_platillo.c.id_option == id_option)
        option_existente = db.execute(stmt_check).fetchone()

        if not option_existente:
            raise HTTPException(status_code=404, detail="No se encontró la opción especificada")

        stmt_delete = delete(opcion_platillo).where(opcion_platillo.c.id_option == id_option)
        db.execute(stmt_delete)
        db.commit()

        return {
            "message": "Opción de personalización eliminada correctamente",
            "id_opcion": id_option
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))