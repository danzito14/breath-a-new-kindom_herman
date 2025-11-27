from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional

class EmpleadosSchema(BaseModel):
    id_puesto: Optional[int] =None
    id_uniforme: Optional[int] =None
    Nombre: Optional[str] =None
    Apellido:Optional[str] =None
    Correo_electronico: Optional[EmailStr] = None
    Num_telefonico: Optional[str] =None
    Calle: Optional[str] =None
    No_ext: Optional[str] =None
    No_int: Optional[str] = None
    Colonia: Optional[str] =None
    CP: Optional[str] =None
    Ciudad: Optional[str] =None
    Municipio: Optional[str] =None
    Estado: Optional[str] =None
    Fecha_de_contratacion: Optional[date] = None
    Fecha_de_despido: Optional[date] = None
    Razon_despido: Optional[str] = None
    Fecha_de_recontratacion: Optional[date] = None
    id_usuario: Optional[str] = None
    estatus: Optional[bool] = None
    Ruta_imagen: Optional[str] =None