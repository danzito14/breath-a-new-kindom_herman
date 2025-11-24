from pydantic import BaseModel, EmailStr
from typing import Optional

class UserSchema(BaseModel):
    id_usuario: Optional[str]=None
    id_nvl_usuario: Optional[str]=None
    Nickname: Optional[str]=None
    Contraseña: Optional[str]=None
    Nombre: Optional[str]=None
    Apellido: Optional[str]=None
    Correo_electronico: Optional[EmailStr]=None
    Num_telefonico: Optional[str] = None
    Ruta_imagen: Optional[str] = None
    estatus: Optional[bool]=None

