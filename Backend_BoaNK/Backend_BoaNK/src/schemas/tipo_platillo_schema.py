from pydantic import BaseModel

class Tipo_platilloSchema(BaseModel):
    descripcion:str
    estatus: bool