import uuid
from datetime import date
from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import select, delete, update, literal, func
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.platillo_model import platillo

""""
    Aqui se la info de los pedidos ya sea para cocinero, mesero, usuario etc
"""

class PedidoService_Gets:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
from sqlalchemy import select, and_, not_

class PedidoService_Gets:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_pedidos_mesero(self):
        query = (
            select(
                mesa.c.id_mesa,
                mesa.c.Nombre_mesa,
                pedido.c.id_pedido,
                pedido.c.Estado.label("estado_pedido"),
                detalle_pedido.c.id_detalle,
                detalle_pedido.c.estado.label("estado_detalle"),
                detalle_pedido.c.detalles_adicionales,
                platillo.c.Nombre_platillo
            )
            .join(pedido, pedido.c.id_mesa == mesa.c.id_mesa)
            .join(detalle_pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
            .join(platillo, platillo.c.id_platillo == detalle_pedido.c.id_platillo)
            .where(
                and_(
                    mesa.c.Estado == "Ocupada",
                    not_(pedido.c.Estado.in_(["Entregado", "Cancelado", "Pagado"])),
                    not_(detalle_pedido.c.estado.in_(["cancelado"]))
                )
            )
        )

        rows = self.db.execute(query).all()

        # ---- Armar respuesta agrupada ----
        mesas_dict = {}

        for r in rows:
            id_mesa = r.id_mesa

            if id_mesa not in mesas_dict:
                mesas_dict[id_mesa] = {
                    "mesa": r.Nombre_mesa,
                    "id_mesa": r.id_mesa,
                    "id_pedido": r.id_pedido,
                    "estado_pedido": r.estado_pedido,
                    "platillos": []
                }

            mesas_dict[id_mesa]["platillos"].append({
                "id_detalle": r.id_detalle,
                "nombre_platillo": r.Nombre_platillo,
                "estado_detalle": r.estado_detalle,
                "detalles_adicionales": r.detalles_adicionales
            })

        return list(mesas_dict.values())

    def cancelar_platillo(self, id_detalle: str, id_pedido: str, id_mesa:str):
        try:
            # 1️⃣ Obtener el precio del detalle
            precio_result = self.db.execute(
                select(detalle_pedido.c.Precio_unitario)
                .where(detalle_pedido.c.id_detalle == id_detalle)
            ).first()

            if not precio_result:
                raise HTTPException(status_code=404, detail="Platillo no encontrado")

            precio_platillo = precio_result[0]

            # 2️⃣ Cancelar este platillo
            self.db.execute(
                update(detalle_pedido)
                .where(detalle_pedido.c.id_detalle == id_detalle)
                .values(estado="cancelado")
            )

            # 3️⃣ Ver cuántos platillos aún NO están cancelados
            platillos_activos = self.db.execute(
                select(func.count()).select_from(detalle_pedido)
                .where(
                    detalle_pedido.c.id_pedido == id_pedido,
                    detalle_pedido.c.estado != "cancelado"
                )
            ).scalar()

            if platillos_activos > 0:
                # 4️⃣ Aún hay platillos activos → solo restamos del total
                self.db.execute(
                    update(pedido)
                    .where(pedido.c.id_pedido == id_pedido)
                    .values(total=pedido.c.total - precio_platillo)
                )
            else:
                # 5️⃣ YA NO QUEDAN PLATILLOS → cancelar pedido completo
                self.db.execute(
                    update(pedido)
                    .where(pedido.c.id_pedido == id_pedido)
                    .values(
                        total=0,
                        Estado="Cancelado"
                    )
                )
                self.db.execute(
                    update(mesa)
                    .where(mesa.c.id_mesa == id_mesa)
                    .values(
                        Estado="Libre"
                    )
                )
            self.db.commit()

            return {
                "message": "Platillo cancelado",
                "pedido_cancelado": platillos_activos == 0
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar platillo: {e}")

    def cancelar_pedido(self, id_pedido: str, id_mesa: str):
        try:
            # 1️⃣ Cancelar todos los platillos del pedido
            self.db.execute(
                update(detalle_pedido)
                .where(detalle_pedido.c.id_pedido == id_pedido)
                .values(estado="cancelado")
            )

            # 2️⃣ Cancelar pedido (total a 0 y estado Cancelado)
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(
                    total=0,
                    Estado="Cancelado"
                )
            )

            # 3️⃣ Liberar la mesa
            self.db.execute(
                update(mesa)
                .where(mesa.c.id_mesa == id_mesa)
                .values(Estado="Libre")
            )

            self.db.commit()

            return {
                "message": "Pedido cancelado correctamente",
                "pedido_cancelado": True
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar pedido: {e}")


