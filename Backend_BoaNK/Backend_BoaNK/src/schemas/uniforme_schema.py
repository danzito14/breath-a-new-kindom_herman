from pydantic import BaseModel, Field
from typing import Literal

class UniformeSchema(BaseModel):
    id_puesto: int
    Talla: Literal['XS', 'S', 'M', 'L', 'XL', 'XXL']
    Descripcion: str = Field(..., max_length=100)
    estatus: bool
