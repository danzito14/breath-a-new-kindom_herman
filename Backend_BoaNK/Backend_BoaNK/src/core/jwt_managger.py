from datetime import datetime, timedelta
# correcto
from jose import jwt

from fastapi import HTTPException

# Configuración
SECRET_KEY = "b7f3e9c2-4a1d-4d6b-9f8e-2c3a7d9e5f1a"  # ⚠️ Cámbiala en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

def create_access_token(id_usuario: str, nvl_usuario: str):
    """
    Crea un JWT con el ID del usuario y su nivel de acceso.
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": id_usuario,
        "nvl_usuario": nvl_usuario,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token