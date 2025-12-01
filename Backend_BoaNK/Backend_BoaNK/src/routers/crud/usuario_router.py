from fastapi import Depends, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from fastapi import File, UploadFile
import os
import uuid
from pathlib import Path
from src.core.jwt_managger import get_current_user
from src.schemas.user_schema import UserSchema
from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db
from passlib.context import CryptContext
from fastapi import Body
from fastapi import APIRouter

from src.services.repositories.usuario_service import UsuarioService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

user = APIRouter(tags=["Usuario"])

@user.get("/")
def root():
    return {"mensage" : "La cabra blanca"}

@user.post("/user/create_user")
def crear_usuario(data: UserSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    service = UsuarioService(db)
    return service.create_user(data)

@user.get("/user/get_all_users")
def get_all_users(db:Session = Depends(get_db)):
    query = db.query(usuarios).all()
    return  [dict(row._mapping) for row in query]

@user.get("/user/get_user_nickname")
def get_user_nickname(Nickname: str, db:Session = Depends(get_db)):
    user = db.query(usuarios).filter(usuarios.c.Nickname == Nickname).first()
    if not user:
        raise  HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user._mapping)

@user.get("/user/get_user_id")
def get_user_nickname(id_usuario: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(usuarios).filter(usuarios.c.id_usuario == id_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user._mapping)


@user.get("/user/get_user_id_adm")
def get_user_nickname(id_usuario: str, db: Session = Depends(get_db)):
    user = db.query(usuarios).filter(usuarios.c.id_usuario == id_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user._mapping)

@user.put("/user/update_user/{nickname}")
def update_user(nickname: str, data_user: UserSchema = Body(...), db: Session = Depends(get_db)):
     # Buscar el usuario existente
    existing_user = db.query(usuarios).filter(usuarios.c.Nickname == nickname).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear diccionario de datos a actualizar (excluyendo los campos vacíos)
    update_data = data_user.dict(exclude_unset=True)

        # Si se está actualizando la contraseña, hay que hashearla
    if "Contraseña" in update_data:
        update_data["Contraseña"] = pwd_context.hash(update_data["Contraseña"])

        # Actualizar el usuario
    try:
        db.query(usuarios).filter(usuarios.c.Nickname == nickname).update(update_data)
        db.commit()
        return {"message": "Usuario actualizado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@user.put("/user/update_user_by_id")
def update_user(
    current_user: str = Depends(get_current_user),
    data_user: UserSchema = Body(...),
    db: Session = Depends(get_db)
):

    update_data = data_user.dict(exclude_unset=True)

    existing_user = db.query(usuarios).filter(usuarios.c.id_usuario == current_user).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar nickname
    if "Nickname" in update_data:
        existe_nick = db.execute(
            select(usuarios).where(
                usuarios.c.Nickname == update_data["Nickname"],
                usuarios.c.id_usuario != current_user
            )
        ).first()

        if existe_nick:
            raise HTTPException(status_code=400, detail="Nickname ya existente, elige otro")

    # Validar correo
    if "Correo_electronico" in update_data:
        existe_correo = db.execute(
            select(usuarios).where(
                usuarios.c.Correo_electronico == update_data["Correo_electronico"],
                usuarios.c.id_usuario != current_user
            )
        ).first()

        if existe_correo:
            raise HTTPException(status_code=400, detail="El correo pertenece a otra cuenta")

    # Hash de contraseña
    if "Contraseña" in update_data:
        update_data["Contraseña"] = pwd_context.hash(update_data["Contraseña"])

    try:
        db.query(usuarios).filter(usuarios.c.id_usuario == current_user).update(update_data)
        db.commit()
        return {"message": "Usuario actualizado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@user.put("/user/update_user_by_id_adm")
def update_user(current_user:str, data_user: UserSchema = Body(...), db: Session = Depends(get_db)):
     # Buscar el usuario existente
    existing_user = db.query(usuarios).filter(usuarios.c.id_usuario == current_user).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear diccionario de datos a actualizar (excluyendo los campos vacíos)
    update_data = data_user.dict(exclude_unset=True)

        # Si se está actualizando la contraseña, hay que hashearla
    if "Contraseña" in update_data:
        update_data["Contraseña"] = pwd_context.hash(update_data["Contraseña"])

        # Actualizar el usuario
    try:
        db.query(usuarios).filter(usuarios.c.id_usuario == current_user).update(update_data)
        db.commit()
        return {"message": "Usuario actualizado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@user.post("/user/actualizar_imagen_perfil")
async def actualizar_imagen_perfil(
    imagen: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validar que sea imagen
        if not imagen.content_type.startswith("image/"):
            raise HTTPException(400, "El archivo debe ser una imagen")

        # Crear carpeta si no existe
        upload_dir = Path("public/profiles")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generar nombre
        ext = os.path.splitext(imagen.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = upload_dir / filename

        # Guardar imagen
        with open(file_path, "wb") as buffer:
            buffer.write(await imagen.read())

        ruta_imagen = f"/public/profiles/{filename}"

        # Actualizar BD
        stmt = text("""
            UPDATE usuarios 
            SET Ruta_imagen = :ruta_imagen 
            WHERE id_usuario = :id_usuario
        """)

        db.execute(stmt, {
            "ruta_imagen": ruta_imagen,
            "id_usuario": current_user
        })
        db.commit()

        return {
            "message": "Imagen actualizada correctamente",
            "ruta": ruta_imagen
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))



@user.post("/user/actualizar_imagen_perfil_adm")
async def actualizar_imagen_perfil(
    current_user: str = Form(...),
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Validar que sea imagen
        if not imagen.content_type.startswith("image/"):
            raise HTTPException(400, "El archivo debe ser una imagen")

        # Crear carpeta si no existe
        upload_dir = Path("public/profiles")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generar nombre
        ext = os.path.splitext(imagen.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = upload_dir / filename

        # Guardar imagen
        with open(file_path, "wb") as buffer:
            buffer.write(await imagen.read())

        ruta_imagen = f"/public/profiles/{filename}"

        # Actualizar BD
        stmt = text("""
            UPDATE usuarios 
            SET Ruta_imagen = :ruta_imagen 
            WHERE id_usuario = :id_usuario
        """)

        db.execute(stmt, {
            "ruta_imagen": ruta_imagen,
            "id_usuario": current_user
        })
        db.commit()

        return {
            "message": "Imagen actualizada correctamente",
            "ruta": ruta_imagen
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(400, str(e))
