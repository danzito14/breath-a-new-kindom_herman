from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

class CocinaSchema(BaseModel):
    id_cocina: str
    id_detalle: str
    id_usuario: str
    estado: Literal['Pendiente', 'En preparación', 'Listo']
    hora_asignacion: datetime
    hora_finalizacion: datetime
    estatus: bool
    carga_tiempo: Optional[int] = None