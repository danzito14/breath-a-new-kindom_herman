from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from typing import Union, List

class OfertasSchema(BaseModel):
    nombre_oferta: str
    descripcion: str
    porcentaje_descuento: Decimal
    fecha_inicio: datetime
    fecha_fin: datetime
    activo: bool

class Oferta_PlatilloSchema(BaseModel):
    id_platillo: Union[str, List[str]]  # ✅ puede ser uno o varios
    id_oferta: str
    activo: bool