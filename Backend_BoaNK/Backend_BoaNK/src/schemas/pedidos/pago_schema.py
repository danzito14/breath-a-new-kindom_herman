from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional, Literal

from sqlalchemy.dialects.mysql import DECIMAL


class PagoSchema(BaseModel):
    id_pago:str
    id_pedido:str
    monto:DECIMAL
    metodo_pago:str
    referencia_pago:str
    estado_pago: Literal['Exitoso', 'Pendiente', 'Fallido']
    fecha_pago: datetime
    pagado_por: Optional[str] = None