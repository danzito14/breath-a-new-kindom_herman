from pydantic import BaseModel, Field
from typing import Optional
class Direcciones_usuarioSchema(BaseModel):
    id_usuario: Optional[str] = Field(None, max_length=36)
    alias: str = Field(..., max_length=50)
    Calle: str = Field(..., max_length=100)
    No_ext: str = Field(..., max_length=10)
    No_int: Optional[str] = Field(None, max_length=10)
    Colonia: str = Field(..., max_length=100)
    CP: str = Field(..., max_length=5)
    Ciudad: Optional[str] = Field(None, max_length=100)  # ✅ Debe permitir None
    Municipio: str = Field(..., max_length=100)
    Estado: str = Field(..., max_length=30)
    predeterminada: bool = Field(
        False,
        description="Si es true, será la dirección predeterminada al comprar."
    )
    instrucciones_add: Optional[str] = Field(None, max_length=200)