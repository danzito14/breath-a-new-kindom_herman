from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional, Literal


class Pedido_Schema(BaseModel):
    id_pedido: Optional[str] = None
    id_usuario: Optional[str] = None
    id_mesa: Optional[str] = None
    id_auto: Optional[str] = None
    total: int
    Fecha: datetime
    Estado: Literal['Pendiente', 'Preparando', 'Listo', 'En camino', 'Entregado', 'Pagada', 'Cancelado']
    Tipo_pedido: Literal['Entrega', 'Local']
    id_direccion: Optional[str] = None

class Detalle_Pedido_Schema(BaseModel):
    id_detalle: str
    id_pedido: str
    id_platillo: str
    Precio_unitario: int
    tiempo_total: int
    estado: Literal['pendiente','cocinando','listo']
    detalles_adicionales: str