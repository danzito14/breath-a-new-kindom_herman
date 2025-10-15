from pydantic import BaseModel, Field

class Tarjetas_PagoSchema(BaseModel):
    id_usuario : str = Field(min_length=36, max_length=36)
    titular: str = Field(..., max_length=100)
    num_tarjeta: str = Field(min_length=19, max_length=19)
    id_tipo_tarjeta: int
    mes_exp:str = Field(min_length=2, max_length=2)
    anio_exp: str = Field(min_length=4, max_length=4)
    predeterminada: bool

class Tipos_TarjetasSchema(BaseModel):
    nombre: str = Field(..., max_length=50)
    categoria: str = Field(..., max_length=20)
