from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from src.routers.crud.usuario_router import user
from src.routers.crud.platillo_router import platillos
from src.routers.crud.empleado_router import empleados
from src.routers.crud.puesto_router import puestos
from src.routers.crud.combos_detallecombo_router import combos
from src.routers.crud.favoritos_router import favorito
from src.routers.crud.tipo_platillo_router import tipo_platillos
from src.routers.crud.automovil_router import automoviles
from src.routers.crud.uniforme_router import uniformes
from src.routers.crud.direcciones_usuario_router import direcciones
from src.routers.crud.tarjeta_tipotarjeta_router import tarjetas
from src.routers.sys.login_router import router
from src.routers.crud.cocineros_router import _cocineros
from src.routers.crud.oferta_router import ofertas
from src.routers.crud.mesa_router import mesas

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
app.include_router(tarjetas)
app.include_router(router)
app.include_router(_cocineros)
app.include_router(ofertas)
app.include_router(mesas)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los headers
)
