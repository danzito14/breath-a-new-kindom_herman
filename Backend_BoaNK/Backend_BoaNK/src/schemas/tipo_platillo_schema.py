from typing import Optional

from pydantic import BaseModel

class Tipo_platilloSchema(BaseModel):
    descripcion:Optional[str] = None
    estatus: Optional[bool]= None
    ruta_icono: Optional[str]= None
    color: Optional[str]= None