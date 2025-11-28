from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

class PlatilloSchema(BaseModel):
    id_tipo_platillo: Optional[int] = None
    Nombre_platillo: Optional[str] = None
    Ruta_imagen: Optional[str] = None
    precio_produccion: Optional[Decimal] = None
    precio_venta: Optional[Decimal] = None
    estatus: Optional[bool] = None
    Descripcion: Optional[str] = None
    tiempo_preparacion: Optional[int] = None

class OpcionplatilloSchema(BaseModel):
    id_platillo: Optional[str] = None
    opcion:Optional[str] = None
    precio: Optional[Decimal] = None




