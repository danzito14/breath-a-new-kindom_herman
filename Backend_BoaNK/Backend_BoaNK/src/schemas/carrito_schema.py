from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

class CarritoSchema (BaseModel):
    id_usuario: str


class DetalleCarrito(BaseModel):
    id_carrito: Optional[str] = None
    id_platillo: str
    precio_unitario: Decimal
    detalles_adicionales: str