from fastapi import APIRouter, Depends, Body, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from pathlib import Path
from datetime import datetime
import uuid
import shutil
import os

from src.db.model.tipo_platillo_model import tipo_platillo
from src.schemas.tipo_platillo_schema import Tipo_platilloSchema
from src.services.repositories.tipo_platillo_service import Tipo_platillosService
from src.core.db_credentials import get_db

tipo_platillos = APIRouter(tags=["Tipo platillo"])

@tipo_platillos.get("/")
def root():
    return {"message":"Ruta Tipo platillos"}

@tipo_platillos.post("/tipo_platillos/create_tipo_platillo", summary="Agregar un tipo platillo nuevo")
def create_tipo_platillo(data:Tipo_platilloSchema, db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return service.create_tipo_platillo(data)

@tipo_platillos.get("/tipo_platillos/get_all_tipo_platillos")
def get_all_tipo_platillos(db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return  service.get_all_tipo_platillo()

@tipo_platillos.put("/tipo_platillos/update_tipo_platillo/{id_tipo_platillo}")
def update_tipo_platillo(id_tipo_platillo: int, data : dict = Body(...), db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return service.update_tipo_platillo(id_tipo_platillo, data)

@tipo_platillos.delete("/tipo_platillos/delete_tipo_platillos/{id_tipo_platillo}")
def delete_tipo_platillo(id_tipo_platillo: int, db: Session = Depends(get_db)):
    service = Tipo_platillosService(db)
    return  service.delete_favorito(id_tipo_platillo)


# --------------------------
# CONFIGURACIÓN DE IMÁGENES
# --------------------------

# CORREGIDO: Usar el path correcto
UPLOAD_DIR = Path("public/icons/icons-food-type")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Usa: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Debe enviarse una imagen")


def generate_unique_filename(original: str):
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}{ext}"


# --------------------------
# SUBIR ICONO
# --------------------------

@tipo_platillos.post("/tipo_platillos/upload_icon/{id_tipo_platillo}", summary="Subir icono de tipo de platillo")
async def upload_icon_tipo_platillo(
        id_tipo_platillo: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        # Validar existencia
        stmt = select(tipo_platillo).where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
        row = db.execute(stmt).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Tipo platillo no encontrado")

        validate_image_file(file)

        # Tamaño
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo excede los 5MB")

        # Guardar
        filename = generate_unique_filename(file.filename)
        path_file = UPLOAD_DIR / filename

        with open(path_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # CORREGIDO: Path relativo correcto
        relative_path = f"public/icons/icons-food-type/{filename}"

        # Actualizar BD
        stmt_up = (
            update(tipo_platillo)
            .where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
            .values(ruta_icono=relative_path)
        )
        db.execute(stmt_up)
        db.commit()

        return {
            "message": "Icono subido correctamente",
            "filename": filename,
            "ruta_icono": relative_path,
            "url": f"/tipo_platillos/icon/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir icono: {str(e)}")
    finally:
        file.file.close()


# --------------------------
# OBTENER ICONO
# --------------------------

@tipo_platillos.get("/tipo_platillos/icon/{filename}")
async def get_icon_tipo_platillo(filename: str):
    path_file = UPLOAD_DIR / filename

    if not path_file.exists():
        raise HTTPException(status_code=404, detail="Icono no encontrado")

    from fastapi.responses import FileResponse
    return FileResponse(path_file)


# --------------------------
# ELIMINAR ICONO
# --------------------------

@tipo_platillos.delete("/tipo_platillos/delete_icon/{filename}")
async def delete_icon_tipo_platillo(filename: str):
    path_file = UPLOAD_DIR / filename

    if not path_file.exists():
        raise HTTPException(status_code=404, detail="Icono no encontrado")

    os.remove(path_file)
    return {"message": "Icono eliminado", "filename": filename}


# --------------------------
# ACTUALIZAR ICONO
# --------------------------

@tipo_platillos.put("/tipo_platillos/update_icon/{id_tipo_platillo}", summary="Actualizar icono")
async def update_icon_tipo_platillo(
        id_tipo_platillo: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        # Verificar que existe
        stmt = select(tipo_platillo).where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
        row = db.execute(stmt).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Tipo platillo no encontrado")

        validate_image_file(file)

        # Tamaño
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)

        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo excede los 5MB")

        # Eliminar icono anterior si existe
        if row.ruta_icono:
            old_file = Path(row.ruta_icono).name
            full_path_old = UPLOAD_DIR / old_file
            if full_path_old.exists():
                os.remove(full_path_old)

        # Guardar nuevo archivo
        filename = generate_unique_filename(file.filename)
        path_file = UPLOAD_DIR / filename

        with open(path_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # CORREGIDO: Path relativo correcto
        relative_path = f"public/icons/icons-food-type/{filename}"

        # Actualizar BD
        stmt_up = (
            update(tipo_platillo)
            .where(tipo_platillo.c.id_tipo_platillo == id_tipo_platillo)
            .values(ruta_icono=relative_path)
        )
        db.execute(stmt_up)
        db.commit()

        return {
            "message": "Icono actualizado correctamente",
            "filename": filename,
            "ruta_icono": relative_path,
            "url": f"/tipo_platillos/icon/{filename}"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar icono: {str(e)}")
    finally:
        file.file.close()