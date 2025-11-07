from datetime import datetime, timedelta
# correcto
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from fastapi import HTTPException, Depends

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

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_user_level(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Devuelve el nivel de usuario (nvl_usuario) a partir del token JWT.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        nvl_usuario: str = payload.get("nvl_usuario")
        if nvl_usuario is None:
            raise HTTPException(status_code=401, detail="Token inválido o sin nivel de usuario")
        return nvl_usuario
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")