from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from passlib.context import CryptContext

from src.core.db_credentials import SessionLocal
from src.db.model.usuario_model import usuarios # tu modelo y sesión
from src.core.jwt_managger import create_access_token  # tu función JWT

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    Nickname: str
    contraseña: str

@router.post("/BoaNK/login")
def login(data: LoginRequest):
    db = SessionLocal()
    try:
        stmt = select(usuarios).where(usuarios.c.Nickname == data.Nickname)
        result = db.execute(stmt).first()

        if not result:
            raise HTTPException(status_code=401, detail="Usuario no registrado")

        user = result._mapping

        if not pwd_context.verify(data.contraseña, user["Contraseña"]):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        if user["estatus"] != 1:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        token = create_access_token(
            id_usuario=user["id_usuario"],
            nvl_usuario=str(user["id_nvl_usuario"])  # lo convertimos a str para el JWT
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "id_usuario": user["id_usuario"],
            "nvl_usuario": user["id_nvl_usuario"],
            "nickname": user["Nickname"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()