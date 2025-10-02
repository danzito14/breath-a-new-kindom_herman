from fastapi import FastAPI
from src.routers.usuario_router import user
from src.routers.platillo_router import platillos
from src.routers.empleado_router import empleados
from src.routers.puesto_router import puestos


app = FastAPI()

app.include_router(user)
app.include_router(platillos)
app.include_router(empleados)
app.include_router(puestos)
