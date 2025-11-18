from typing import Literal, Optional

from pydantic import BaseModel

class RepartidorSchema(BaseModel):
    id_repartidor: str
    id_usuario: str
    activo: bool
    en_ruta: bool
    pedidos_asignados: int
    estado: Literal['En local', 'Repartiendo']
    id_pedido: str