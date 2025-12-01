from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fastapi.responses import RedirectResponse, HTMLResponse

from src.core.db_credentials import get_db
from src.services.system.email.activar_cuenta_service import activar_cuentaService

cuenta = APIRouter()

class activar_cuenta(BaseModel):
    correo: str
    codigo: str


# --- Activar cuenta desde la API (por formulario o Angular, método PUT) ---
@cuenta.put("/cuenta/activar_cuenta", summary="Activar cuenta desde la app")
def activarcuenta(data: activar_cuenta, db: Session = Depends(get_db)):
    service_cuenta = activar_cuentaService(db)
    return service_cuenta.activar_cuenta(data.correo, data.codigo)


# --- Activar cuenta desde el correo (método GET) ---
@cuenta.get("/cuenta/activar_cuenta", summary="Activar cuenta desde correo")
def activar_cuenta_por_link(correo: str, codigo: str, db: Session = Depends(get_db)):
    service_cuenta = activar_cuentaService(db)
    resultado = service_cuenta.activar_cuenta(correo, codigo)

    if resultado["exito"]:
        return RedirectResponse(url="https://restaurantbreathofanewkindom.up.railway.app/login")
    else:
        return RedirectResponse(url="https://restaurantbreathofanewkindom.up.railway.app/auth-error")
