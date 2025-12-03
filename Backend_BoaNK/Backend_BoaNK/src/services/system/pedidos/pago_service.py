from datetime import datetime
import uuid
from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from typing import Optional

from src.core.db_credentials import get_db
from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pago_model import pago
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido

from src.services.system.repartidores.repartidores_service import RepartidorService

# 🔥 IMPORTAR EL GESTOR DE WEBSOCKET
from src.core.websocket_manager import manager


class Pago_Service:
    def __init__(self, db: Session = Depends(get_db),
                 background_tasks: Optional[BackgroundTasks] = None):
        self.db = db
        self.background_tasks = background_tasks

    def registrar_pago(
        self,
        id_usuario: str,
        id_pedido: str,
        metodo_pago: str,
        id_mesa: str,
        referencia_pago: str = None
    ):
        """
        Registra el pago de un pedido si todos los platillos ya están servidos o cancelados.
        """

        # 1️⃣ Verificar que el pedido esté listo para pagar
        if not self.verificar_estado_pedido(id_pedido):
            raise HTTPException(
                status_code=400,
                detail="No se puede pagar: aún faltan platillos por terminar. Cancele los pendientes para proceder."
            )

        # 2️⃣ Obtener el total del pedido y el nombre de la mesa
        pedido_info = self.db.execute(
            select(pedido.c.total, pedido.c.Tipo_pedido)
            .where(pedido.c.id_pedido == id_pedido)
        ).first()

        if pedido_info is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        total_pagar = pedido_info.total
        tipo_pedido = pedido_info.Tipo_pedido

        # Obtener nombre de la mesa si existe
        nombre_mesa = None
        if id_mesa:
            nombre_mesa = self.db.execute(
                select(mesa.c.Nombre_mesa).where(mesa.c.id_mesa == id_mesa)
            ).scalar()

        # 3️⃣ Crear el registro del pago
        nuevo_pago = {
            "id_pago": str(uuid.uuid4()),
            "id_pedido": id_pedido,
            "monto": total_pagar,
            "metodo_pago": metodo_pago,
            "referencia_pago": referencia_pago or f"REF-{uuid.uuid4().hex[:8].upper()}",
            "estado_pago": "Exitoso",
            "fecha_pago": datetime.now(),
            "pagado_por": id_usuario
        }

        # 4️⃣ Insertar el pago
        self.db.execute(pago.insert().values(**nuevo_pago))

        # 5️⃣ Actualizar el estado del pedido
        self.db.execute(
            update(pedido)
            .where(pedido.c.id_pedido == id_pedido)
            .values(
                Estado="Pagada",
                fecha_pago=datetime.now()
            )
        )

        # 6️⃣ Liberar la mesa si existe
        if id_mesa:
            self.db.execute(
                update(mesa)
                .where(mesa.c.id_mesa == id_mesa)
                .values(Estado="Libre")
            )

        # 7️⃣ Verificar si es entrega y actuar
        self.verificar_si_es_entrega_y_actuar(id_pedido, id_usuario)

        # 8️⃣ Confirmar transacción
        self.db.commit()

        # 🔥 9️⃣ NOTIFICAR VÍA WEBSOCKET A LOS MESEROS
        if self.background_tasks:
            self.background_tasks.add_task(
                self._notificar_pago_completado_async,
                id_pedido,
                id_mesa,
                nombre_mesa,
                tipo_pedido,
                total_pagar,
                metodo_pago
            )

        # 🔟 Devolver respuesta al cliente
        return {
            "mensaje": "Pago registrado exitosamente",
            "data": nuevo_pago
        }

    # 🔥 MÉTODO PARA NOTIFICAR VÍA WEBSOCKET
    async def _notificar_pago_completado_async(
        self,
        id_pedido: str,
        id_mesa: str,
        nombre_mesa: str,
        tipo_pedido: str,
        total: float,
        metodo_pago: str
    ):
        """Notifica a los meseros que se completó un pago y la mesa está libre"""
        try:
            mensaje = {
                "tipo": "pago_completado",
                "id_pedido": id_pedido,
                "id_mesa": id_mesa,
                "nombre_mesa": nombre_mesa,
                "tipo_pedido": tipo_pedido,
                "total": float(total),
                "metodo_pago": metodo_pago,
                "timestamp": datetime.now().isoformat()
            }

            # Enviar notificación a todos los meseros conectados
            await manager.broadcast_to_group(mensaje, "meseros")
            await manager.broadcast_to_group(mensaje, "admin")
            print(f"✅ Notificación de pago enviada a meseros: Mesa {nombre_mesa}")

        except Exception as e:
            print(f"❌ Error al enviar notificación de pago: {e}")

    def verificar_estado_pedido(self, id_pedido: str) -> bool:
        """
        Devuelve True si todos los platillos del pedido están 'Servido' o 'Cancelado'.
        """
        estados_no_finales = {'pendiente', 'cocinando'}

        query = select(func.count()).select_from(detalle_pedido).where(
            detalle_pedido.c.id_pedido == id_pedido,
            detalle_pedido.c.estado.in_(estados_no_finales)
        )

        result = self.db.execute(query).scalar()
        return result == 0

    def get_total_pedido(self, id_pedido):
        total_pagar = self.db.execute(
            select(pedido.c.total).where(pedido.c.id_pedido == id_pedido)
        ).scalar()
        return total_pagar

    def verificar_si_es_entrega_y_actuar(self, id_pedido: str, id_usuario: str):
        # 1️⃣ ¿Es pedido de entrega?
        tipo = self.db.execute(
            select(pedido.c.Tipo_pedido).where(pedido.c.id_pedido == id_pedido)
        ).scalar()

        if tipo != "Entrega":
            return

        # 2️⃣ Marcar todos los platillos como servidos
        self.db.execute(
            update(detalle_pedido)
            .where(detalle_pedido.c.id_pedido == id_pedido)
            .values(estado="servido")
        )

        # 3️⃣ Quitar el pedido del repartidor
        serviceRepartidores = RepartidorService(self.db)
        serviceRepartidores.finalizar_pedido(id_pedido, id_usuario)