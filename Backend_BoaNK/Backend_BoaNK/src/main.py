from fastapi import FastAPI

from src.routers.usuario_router import user
from src.routers.platillo_router import platillos
from src.routers.empleado_router import empleados
from src.routers.puesto_router import puestos
from src.routers.combos_detallecombo_router import combos
from src.routers.favoritos_router import favorito
from src.routers.tipo_platillo_router import tipo_platillos
from src.routers.automovil_router import automoviles
from src.routers.uniforme_router import uniformes
from src.routers.direcciones_usuario_router import direcciones

app = FastAPI()

app.include_router(user)
app.include_router(platillos)
app.include_router(empleados)
app.include_router(puestos)
app.include_router(combos)
app.include_router(favorito)
app.include_router(tipo_platillos)
app.include_router(automoviles)
app.include_router(uniformes)
app.include_router(direcciones)
