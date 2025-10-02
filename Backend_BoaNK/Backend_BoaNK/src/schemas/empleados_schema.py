from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional

class EmpleadosSchema(BaseModel):
    id_puesto: int
    id_uniforme: int
    Nombre: str
    Apellido:str
    Correo_electronico: EmailStr
    Num_telefonico: str
    Calle: str
    No_ext: str
    No_int: Optional[str] = None
    Colonia: str
    CP: str
    Ciudad: str
    Municipio: str
    Estado: str
    Fecha_de_contratacion: Optional[date] = None
    Fecha_de_despido: Optional[date] = None
    Razon_despido: Optional[str] = None
    Fecha_de_recontratacion: Optional[date] = None
    id_usuario: Optional[str] = None
    estatus: bool
    Ruta_imagen: str