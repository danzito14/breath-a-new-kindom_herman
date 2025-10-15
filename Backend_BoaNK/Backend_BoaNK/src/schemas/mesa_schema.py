from pydantic import  BaseModel, Field
from typing import Literal

class MesaSchema(BaseModel):
    Capacidad: int
    Estado: Literal['Libre', 'Ocupada', 'Reservada']
    estatus_bool: bool