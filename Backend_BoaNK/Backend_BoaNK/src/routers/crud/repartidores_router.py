from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user, get_user_level
from src.services.system.repartidores.repartidores_service import RepartidorService
from src.services.repositories.repartidores_service import RepartidoresService as Repartidores_Services_Repositorie

repartidor_router = APIRouter(prefix="/repartidores", tags=["Repartidores"])


class AsignarPedidoRequest(BaseModel):
    id_pedido: str


class MarcarEntregadoRequest(BaseModel):
    id_pedido: str
    id_repartidor: str

@repartidor_router.put("/update_repartidor", summary="Actualizar datos del repartidor")
def update_repartidor(data:dict,current_user: str = Depends(get_current_user), db:Session = Depends(get_db)):
    service = Repartidores_Services_Repositorie(db)
    id_usuario = current_user
    return  service.update_repartidores(id_usuario, data)

@repartidor_router.get("/disponibles", summary="Obtener todos los repartidores disponibles")
def obtener_repartidores_disponibles(
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level)
):
    """
    Lista todos los repartidores activos con sus pedidos asignados.
    Acceso: Admin (6), Cajero (4), Mesero (2), Cliente(1)
    """
    # Validar nivel de acceso
    if int(nvl_usuario) not in [1, 2, 4, 6]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver repartidores")

    service = RepartidorService(db)
    return service.obtener_repartidores_disponibles()


@repartidor_router.post("/asignar-pedido", summary="Asignar pedido con IA")
async def asignar_pedido_con_ia(
        request: AsignarPedidoRequest,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level)
):
    """
    Asigna un pedido al repartidor más adecuado usando Gemini AI.
    Considera: distancia, carga de trabajo y rutas existentes.
    Acceso: Admin (6), Cajero (4), Mesero (2), Cliente(1), Repartidor(5)
    """
    # Solo admin y cajero pueden asignar pedidos
    if int(nvl_usuario) not in [1, 2, 4, 6]:
        raise HTTPException(status_code=403, detail="No tienes permisos para asignar pedidos")

    service = RepartidorService(db)
    return await service.asignar_pedido_con_ia(request.id_pedido)

""""
@repartidor_router.put("/marcar-entregado", summary="Marcar pedido como entregado")
def marcar_pedido_entregado(
        request: MarcarEntregadoRequest,
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level)
):Marca un pedido como entregado y actualiza el estado del repartidor.
    Acceso: Admin (6), Cajero (4), Mesero (2), Cliente(1), Repartidor(5)
    # Validar permisos
    if int(nvl_usuario) not in [1, 2, 4, 6 ]:
        # Si no es admin/cajero, verificar que sea el repartidor del pedido
        # Aquí podrías agregar lógica adicional si los repartidores tienen acceso
        raise HTTPException(status_code=403, detail="No tienes permisos para marcar entregas")

    service = RepartidorService(db)
    return service.marcar_pedido_entregado(request.id_pedido, request.id_repartidor)

    """

@repartidor_router.get("/{id_repartidor}/pedidos", summary="Obtener pedidos de un repartidor")
def obtener_pedidos_repartidor(
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level)
):
    """
    Obtiene todos los pedidos asignados a un repartidor específico.
    Acceso: Admin (6), Cajero (4), Mesero (2), Cliente(1), Repartidor(5)
    """
    if int(nvl_usuario) not in [1, 2, 4, 6]:
        raise HTTPException(status_code=403, detail="No tienes permisos")
    id_repartidor = user_id
    service = RepartidorService(db)
    return service._obtener_pedidos_repartidor(id_repartidor)


# AGREGAR ESTE ENDPOINT A src/routers/sys/repartidor_routes.py

@repartidor_router.get("/info", summary="Obtener información del repartidor por ID de usuario")
def obtener_info_repartidor_por_usuario(
        db: Session = Depends(get_db),
        user_id: str = Depends(get_current_user),
        nvl_usuario: str = Depends(get_user_level)
):
    """
    Obtiene la información de un repartidor basándose en su ID de usuario.
    Útil para que el repartidor vea su propia información.
    Acceso: Admin (6), Cajero (4), Repartidor (propio)
    """

    id_usuario = user_id
    # Validar que solo pueda ver su propia info (excepto admin/cajero)
    if int(nvl_usuario) not in [4, 6] and user_id != id_usuario:
        raise HTTPException(status_code=403, detail="Solo puedes ver tu propia información")

    service = RepartidorService(db)
    repartidores = service.obtener_repartidores_disponibles()

    # Buscar el repartidor con ese id_usuario
    repartidor = next((r for r in repartidores if r['id_usuario'] == id_usuario), None)

    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado")

    return repartidor