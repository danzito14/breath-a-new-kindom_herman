from decimal import Decimal
from pydantic import BaseModel

class ComboSchema(BaseModel):
    Nombre_combo: str
    Descripcion: str
    Ruta_imagen: str
    precio_combo: Decimal
    estatus: bool

class ComboDetalleSchema(BaseModel):
    id_combo: str
    id_platillo: str
    Cantidad: int


