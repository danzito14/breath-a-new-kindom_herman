from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class PuestoSchema(BaseModel):
    Nombre_puesto: Optional[str] = None
    Sueldo: Optional[Decimal] = None
    estatus: Optional[bool] = None
    id_nvl_usuario: Optional[int] = None
