from decimal import Decimal
from pydantic import BaseModel

class PuestoSchema(BaseModel):
        Nombre_puesto: str
        Sueldo: Decimal
        estatus: bool
        id_nvl_usuario: int