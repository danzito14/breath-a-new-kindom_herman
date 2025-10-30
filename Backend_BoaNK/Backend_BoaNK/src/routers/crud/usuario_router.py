from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

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