from decimal import Decimal
from pydantic import BaseModel
from typing import  Optional

class ComboSchema(BaseModel):
    Nombre_combo: Optional[str] =None
    Descripcion: Optional[str] =None
    Ruta_imagen: Optional[str] =None
    precio_combo: Optional[Decimal] =None
    estatus: Optional[bool] =None

class ComboDetalleSchema(BaseModel):
    id_combo: Optional[str] = None
    id_platillo: Optional[str] =None
    Cantidad: Optional[int]=None


