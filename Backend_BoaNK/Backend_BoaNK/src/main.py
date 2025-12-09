from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os


# ✅ Cargar el archivo .env
load_dotenv()

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
from src.routers.sys.activar_cuenta import cuenta
from src.routers.sys.home_router import home
from src.routers.sys.login_router import router
from src.routers.crud.cocineros_router import _cocineros
from src.routers.crud.repartidores_router import repartidor_router
from src.routers.crud.oferta_router import ofertas
from src.routers.crud.mesa_router import mesas
from src.routers.crud.carrito_router import carrito
from src.services.system.reportes.reportes_ventas import reportes
from src.routers.sys.pedidos.pago_router import pago_router
from src.routers.sys.pedidos.pedido_gets_router import pedido_gets
from src.routers.sys.pedidos.pedidos_temporal_router import temporal
from src.routers.sys.pedidos.registrar_pedido_router import registar
from src.routers.sys.websocket_router import websocket_router
from src.utils.cp_router import utils
from src.utils.utils_empleados import untils_empleados
from src.services.system.reportes.mineria_datos import mineria

from src.utils.recomendacion_router import router_recomendar


app = FastAPI()


# Servir carpeta /public
app.mount("/public", StaticFiles(directory="public"), name="public")

# Primero CORS
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", '*'],  # ambos por seguridad
    allow_origins=['*'],  # ambos por seguridad
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(cuenta)
app.include_router(home)
app.include_router(carrito)
app.include_router(temporal)
app.include_router(utils)
app.include_router(registar)
app.include_router(untils_empleados)
app.include_router(pedido_gets)
app.include_router(pago_router)
app.include_router(websocket_router)
app.include_router(repartidor_router)
app.include_router(reportes)
app.include_router(mineria)
app.include_router(router_recomendar)
