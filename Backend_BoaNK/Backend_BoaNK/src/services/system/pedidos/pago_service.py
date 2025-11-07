from datetime import datetime
import uuid
from fastapi import Depends, HTTPException
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pago_model import pago
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido


class Pago_Service:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

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

        # 2️⃣ Obtener el total del pedido
        total_pagar = self.db.execute(
            select(pedido.c.total).where(pedido.c.id_pedido == id_pedido)
        ).scalar()

        if total_pagar is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")

        # 3️⃣ Crear el registro del pago
        nuevo_pago = {
            "id_pago": str(uuid.uuid4()),
            "id_pedido": id_pedido,
            "monto": total_pagar,
            "metodo_pago": metodo_pago,
            "referencia_pago": referencia_pago or f"REF-{uuid.uuid4().hex[:8].upper()}",
            "estado_pago": "Exitoso",  # podrías usar "Pendiente" si esperas confirmación externa
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
        self.db.execute(
            update(mesa)
            .where(mesa.c.id_mesa == id_mesa)
            .values(
                Estado="Libre"
            )
        )

        # 6️⃣ Confirmar transacción
        self.db.commit()

        # 7️⃣ Devolver respuesta al cliente
        return {
            "mensaje": "Pago registrado exitosamente",
            "data": nuevo_pago
        }

    def verificar_estado_pedido(self, id_pedido: str) -> bool:
        """
        Devuelve True si todos los platillos del pedido están 'Servido' o 'Cancelado'.
        """
        estados_no_finales = {'pendiente', 'cocinando', 'listo'}  # ajusta a tus valores reales

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
        return  total_pagar
