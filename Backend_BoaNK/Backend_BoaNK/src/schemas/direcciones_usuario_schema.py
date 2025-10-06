from pydantic import BaseModel, Field
from typing import Optional
class Direcciones_usuarioSchema(BaseModel):
    id_usuario: str = Field(..., max_legth=36),
    alias: str = Field(..., max_length=50),
    Calle: str = Field(..., max_length=100),
    No_ext: str = Field(..., max_length=10),
    No_int: Optional[str] = Field(None, max_length=10),
    Colonia: str = Field(..., max_length=100),
    CP: str = Field(..., max_length=5),
    Ciudad: str = Field(..., max_length=100),
    Municipio: str = Field(..., max_length=100),
    Estado: str =Field(..., max_length= 30),
    predeterminada: bool = Field(True,
                                 description="Si predeterminada es true, sera la que salga por default al comprar")