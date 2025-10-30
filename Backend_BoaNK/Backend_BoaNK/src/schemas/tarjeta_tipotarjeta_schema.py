from typing import Optional

from pydantic import BaseModel, Field

class Tarjetas_PagoSchema(BaseModel):
    id_usuario : Optional[str] = None
    titular: str = Field(..., max_length=100)
    num_tarjeta: str = Field(min_length=4, max_length=4)
    id_tipo_tarjeta: Optional[int] = None
    fecha_exp:str = Field(min_length=5, max_length=5)

class Tipos_TarjetasSchema(BaseModel):
    nombre: str = Field(..., max_length=50)
    categoria: str = Field(..., max_length=20)
