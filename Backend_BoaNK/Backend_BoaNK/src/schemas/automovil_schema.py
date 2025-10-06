from pydantic import BaseModel, Field
from typing import Literal
from datetime import date

class AutomovilSchema(BaseModel):

    Marca: str
    Modelo: str
    Año: int = Field(..., ge=1990, le=2100, description="Año del automóvil")
    Placas: str = Field(..., max_length=10)
    Color: str = Field(..., max_length=30)
    Fecha_compra: date
    Estado: Literal["Activo", "En mantenimiento", "Baja"]
    id_empleado: str
    apodo: str

    class Config:
        orm_mode = True
