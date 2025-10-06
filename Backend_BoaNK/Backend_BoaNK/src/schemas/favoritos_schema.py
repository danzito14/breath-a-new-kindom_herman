from datetime import date
from pydantic import BaseModel

class FavoritosSchema(BaseModel):
    id_usuario: str
    id_platillo: str
    fecha_agregado: date