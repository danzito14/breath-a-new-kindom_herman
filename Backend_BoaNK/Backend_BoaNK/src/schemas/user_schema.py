from pydantic import BaseModel, EmailStr
from typing import Optional

class UserSchema(BaseModel):
    id_usuario: Optional[str]=None
    id_nvl_usuario: int
    Nickname: str
    Contraseña: str
    Nombre: str
    Apellido: str
    Correo_electronico: EmailStr
    Num_telefonico: str
    Ruta_imagen: Optional[str] = None
    estatus: bool

