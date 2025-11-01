from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Body
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user
from src.schemas.carrito_schema import CarritoSchema, DetalleCarrito
from src.services.repositories.carrito_service import CarritoService

carrito = APIRouter(prefix="/carrito", tags=["Carrito"])


# 🛒 Crear carrito manualmente (normalmente no se necesita)
@carrito.post("/create", summary="Crear carrito de un usuario")
def create_carrito(data: CarritoSchema, service: CarritoService = Depends()):
    """
    Crea un carrito vacío para el usuario especificado.
    Si ya existe, devuelve error 409.
    """
    try:
        result = service.get_or_create_carrito(data.id_usuario)
        return {
            "message": "Carrito creado correctamente",
            "id_carrito": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ➕ Agregar platillo al carrito (crea carrito si no existe)
@carrito.post("/agregar", summary="Agregar platillo al carrito")
def agregar_platillo(
    id_usuario: str = Depends(get_current_user),
    data: DetalleCarrito = Body(...),
    service: CarritoService = Depends()
):
    """
    Agrega un platillo al carrito del usuario.
    Si el carrito no existe, lo crea automáticamente.
    """
    try:
        result = service.agregar_platillo_carrito(id_usuario, data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 🔍 Obtener todos los platillos de un carrito por usuario
@carrito.get("/get_by_user", summary="Obtener carrito del usuario logueado")
def get_carrito_by_user(
    id_usuario: str = Depends(get_current_user),
    service: CarritoService = Depends()
):
    try:
        result = service.get_carrito_by_user(id_usuario)
        if not result:
            return {"message": "Carrito vacío o no encontrado", "platillos": []}
        return {"platillos": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@carrito.post("/get_by_ids", summary="Obtener por lista de IDs")
def get_carrito_by_ids(data: List[str], db: Session = Depends(get_db)):
    service = CarritoService(db)
    return service.get_carrito_by_ids(data)

# ❌ Eliminar un platillo específico del carrito
@carrito.delete("/eliminar/{id_detalle_carrito}", summary="Eliminar platillo del carrito")
def eliminar_platillo(id_detalle_carrito: str, service: CarritoService = Depends()):
    """
    Elimina un platillo del carrito por su id_detalle_carrito.
    """
    try:
        result = service.eliminar_platillo(id_detalle_carrito)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 🧹 Vaciar todo el carrito de un usuario
@carrito.delete("/vaciar/{id_usuario}", summary="Vaciar carrito completo")
def vaciar_carrito(id_usuario: str, service: CarritoService = Depends()):
    """
    Elimina todos los platillos del carrito del usuario especificado.
    """
    try:
        result = service.vaciar_carrito_usuario(id_usuario)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
