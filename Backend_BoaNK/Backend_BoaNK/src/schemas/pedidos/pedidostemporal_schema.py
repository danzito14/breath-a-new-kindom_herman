from datetime import datetime

from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

from decimal import Decimal


class pedido_temporalSchema(BaseModel):
    id_usuario: Optional[str] = None
    datos_pedido: Optional[Any] = None
    fecha_creacion: Optional[datetime] = None
    precio: Optional[float] = None
    lista_producto: Optional[List[Dict[str, Any]]] = None
    metodo_pago: Optional[str] = None
    id_tarjeta: Optional[str] = None
    direccion: Optional[str] = None
    id_mesa: Optional[str] = None
    id_direccion: Optional[str] = None
