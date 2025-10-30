from datetime import datetime

from pydantic import BaseModel

class Activar_CuentaSchema(BaseModel):
    correo_electronico: str
    codigo: str
    create_at: datetime
    expira_at: datetime