from decimal import Decimal
from pydantic import BaseModel

class PlatilloSchema(BaseModel):
    id_tipo_platillo: int
    Nombre_platillo: str
    Ruta_imagen: str
    precio_produccion: Decimal
    precio_venta: Decimal
    estatus: bool
    Descripcion: str
    tiempo_preparacion: int





