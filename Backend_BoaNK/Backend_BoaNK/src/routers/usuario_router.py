from cryptography.utils import deprecated
from fastapi import APIRouter, Depends, HTTPException
from passlib.handlers.bcrypt import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import insert, select
from sqlalchemy.exc import SQLAlchemyError
from src.schemas.user_schema import UserSchema
from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db
from passlib.context import CryptContext
import uuid
from fastapi import Body


pwd_context = CryptContext(schemes=[bcrypt], deprecated="auto")

user = APIRouter()

@user.get("/")
def root():
    return {"mensage" : "La cabra blanca"}

@user.post("/api/create_user")
def create_user(data_user: UserSchema, db: Session = Depends(get_db)):
    #validar el correo
    existing_correo = db.execute(
        select(usuarios).where(usuarios.c.Correo_electronico == data_user.Correo_electronico)
    ).first()
    if existing_correo:
        raise HTTPException(status_code=400, detail=str("Correo electronico ya registrado"))

    existing_user = db.execute(
        select(usuarios).where(usuarios.c.Nickname == data_user.Nickname)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=str("Nickname ya existente"))

    #Hashear la contraseña
    hased_password = pwd_context.hash((data_user.Contraseña))

    # Generar el id
    user_dict = data_user.dict(exclude_unset=True)
    user_dict["id_usuario"] = str(uuid.uuid4())
    user_dict["Contraseña"] = hased_password

    stmt = insert(usuarios).values(**user_dict)
    try:
        db.execute(stmt)
        db.commit()
        return {"message":"Usuario creado correctamente", "nombre" :user_dict["Nombre"]}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@user.get("/api/get_all_users")
def get_all_users(db:Session = Depends(get_db)):
    query = db.query(usuarios).all()
    return  [dict(row._mapping) for row in query]

@user.get("/api/get_user_nickname")
def get_user_nickname(Nickname: str, db:Session = Depends(get_db)):
    user = db.query(usuarios).filter(usuarios.c.Nickname == Nickname).first()
    if not user:
        raise  HTTPException(status_code=404, detail="Usuario no encontrado")
    return dict(user._mapping)

@user.put("/api/update_user/{nickname}")
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