from decimal import Decimal
from pydantic import BaseModel
from typing import  Optional

class ComboSchema(BaseModel):
    Nombre_combo: str
    Descripcion: str
    Ruta_imagen: str
    precio_combo: Decimal
    estatus: bool

class ComboDetalleSchema(BaseModel):
    id_combo: Optional[str] = None
    id_platillo: str
    Cantidad: int


