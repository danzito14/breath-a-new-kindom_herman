import uuid

from typing import List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy import select, delete, update, literal, func, desc, case, text
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.db.model.direcciones_usuario_model import direcciones_usuario
from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.platillo_model import platillo
from src.db.model.usuario_model import usuarios

""""
    Aqui se la info de los pedidos ya sea para cocinero, mesero, usuario etc
"""

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
                    not_(pedido.c.Estado.in_(["Entregado", "Cancelado", "Pagada"])),
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

    def cancelar_platillo(self, id_detalle: str, id_pedido: str, id_mesa: Optional[str] = None):
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
                if id_mesa is not None:
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
            # Obtener id_usuario del pedido
            result = self.db.execute(
                select(pedido.c.id_usuario, pedido.c.id_direccion)
                .where(pedido.c.id_pedido == id_pedido)
            ).first()

            if not result:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            id_usuario_del_pedido, id_direccion_pedido = result

            # Verificar nivel del usuario
            nivel_usuario = self.db.execute(
                select(usuarios.c.id_nvl_usuario)
                .where(usuarios.c.id_usuario == id_usuario_del_pedido)
            ).scalar()

            ID_USUARIO_GENERICO = '00000000-0000-0000-0000-000000000001'
            ID_DIRECCION_GENERICA = '00000000-0000-0000-0000-00000000000A'
            # Si es temporal (nivel 8)
            if nivel_usuario == 8:

                # 1) Cambiar el pedido a usuario y dirección genéricos
                self.db.execute(
                    update(pedido)
                    .where(pedido.c.id_pedido == id_pedido)
                    .values(
                        id_usuario=ID_USUARIO_GENERICO,
                        id_direccion=ID_DIRECCION_GENERICA,
                        total=0,
                        Estado="Cancelado"
                    )
                )

                # 2) Eliminar direcciones del usuario temporal
                self.db.execute(
                    delete(direcciones_usuario)
                    .where(direcciones_usuario.c.id_usuario == id_usuario_del_pedido)
                )

                # 3) Eliminar usuario temporal
                self.db.execute(
                    delete(usuarios)
                    .where(usuarios.c.id_usuario == id_usuario_del_pedido)
                )

            else:
                # Solo cancelar sin borrar
                self.db.execute(
                    update(detalle_pedido)
                    .where(detalle_pedido.c.id_pedido == id_pedido)
                    .values(estado="cancelado")
                )

                self.db.execute(
                    update(pedido)
                    .where(pedido.c.id_pedido == id_pedido)
                    .values(
                        total=0,
                        Estado="Cancelado"
                    )
                )

            # 4) Liberar mesa
            self.db.execute(
                update(mesa)
                .where(mesa.c.id_mesa == id_mesa)
                .values(Estado="Libre")
            )

            self.db.commit()

            return {"message": "Pedido cancelado correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar pedido: {e}")

    """
        Para mostrar los pedidos de mesa y a domicilio,
        seria primero definir quien puede ver todo eso:
        Administrador, Cajero 
        Eso lo defino en el front al cargar la pagina y ver quien es quien si nvl_usuario = 4,6 mostraremos todo
        Con eso definido entonces, vamos a ver que ocupa el front
            --> Mesas
            --> Domicilio (tanto creados por el mismo cajero como los que han hecho el usuario)
                        Entonces aqui seria una funcion que cargue todos los pedidos a domcilio pendientes
                                Condition: Estado-pedido = all execpt(entregado, pagado, cancelado), Tipo pedido: Entrega
                        OK con eso definido se tiene que hacer una funcion que haga eso y en el front hacemos dos llamados segun el nvl usuario que tenga 
        Si es un mesero solo vera
            --> Mesas
        Caso contrario con en usuario
            --> Domiciliio ( todos los que pertenezcan al usuario y esten aun pendeintes de entregar o no esten cancelados)

        Funciones necesarias:
            Pedidos por mesa: get_pedidos_mesero() esa ya la tenia hecha
            Pedidos domicilio absolute: pendiente es el que me mostrara tanto para usuarios comun como usuarios normales
            Pedidos by id usuario: pendeinte el nombre explica todo get_pedido_by_id_usuario
    """

    # Primero hacemos el pedidos absolute

    def get_pedidos_absolute(self):
        direccion_label = case(
            (direcciones_usuario.c.temporal == True, direcciones_usuario.c.instrucciones_add),
            else_=func.concat(
                direcciones_usuario.c.Calle, " ",
                direcciones_usuario.c.No_ext, ", ",
                direcciones_usuario.c.No_int, ", ",
                direcciones_usuario.c.Colonia, ", ",
                direcciones_usuario.c.Ciudad, ", ",
                direcciones_usuario.c.Estado, ", CP ",
                direcciones_usuario.c.CP, " ",
                direcciones_usuario.c.instrucciones_add
            )
        ).label("direccion_completa")
        query = (
            select(
                usuarios.c.id_usuario,
                func.concat(usuarios.c.Nombre, " ", usuarios.c.Apellido).label("nombre_completo"),
                pedido.c.id_pedido,
                pedido.c.Estado.label("estado_pedido"),
                pedido.c.Fecha,
                pedido.c.Tipo_pedido,
                pedido.c.total,
                pedido.c.id_direccion,
                detalle_pedido.c.id_detalle,
                detalle_pedido.c.estado.label("estado_detalle"),
                detalle_pedido.c.detalles_adicionales,
                platillo.c.Nombre_platillo,
                direccion_label  # ✅ Concatenamos la dirección completa (para Google Maps)

            )
            .join(pedido, pedido.c.id_usuario == usuarios.c.id_usuario)
            .join(detalle_pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
            .join(platillo, platillo.c.id_platillo == detalle_pedido.c.id_platillo)
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .where(
                and_(
                    pedido.c.Tipo_pedido == "Entrega",
                    pedido.c.Estado.notin_(["Entregado", "Cancelado", "Pagada"]),
                    detalle_pedido.c.estado.notin_(["cancelado"])
                )
            )
            .order_by(desc(pedido.c.Fecha))
        )

        rows = self.db.execute(query).all()

        # ---- Agrupar por pedido ----
        pedidos_dict = {}

        for r in rows:
            id_pedido = r.id_pedido

            if id_pedido not in pedidos_dict:
                pedidos_dict[id_pedido] = {
                    "id_pedido": r.id_pedido,
                    "fecha": r.Fecha,
                    "estado_pedido": r.estado_pedido,
                    "tipo_pedido": r.Tipo_pedido,
                    "id_usuario": r.id_usuario,
                    "nombre_completo": r.nombre_completo,
                    "total": r.total,
                    "id_direccion": r.id_direccion,
                    "direccion_completa": r.direccion_completa,  # ✅ lista para Google Maps
                    "platillos": []
                }

            pedidos_dict[id_pedido]["platillos"].append({
                "id_detalle": r.id_detalle,
                "nombre_platillo": r.Nombre_platillo,
                "estado_detalle": r.estado_detalle,
                "detalles_adicionales": r.detalles_adicionales
            })

        return list(pedidos_dict.values())

    def get_platillos_pendientes(self):

        query = text("""
                SELECT * FROM vista_pedido_detalle_destino where estado = 'pendiente' order by Fecha ASC
        """)
        result = self.db.execute(query)

        return [dict(row._mapping) for row in result]

    def get_platillos_listos(self):

        query = text("""
                  SELECT * FROM vista_pedido_detalle_destino where estado = 'listo' order by Fecha ASC
          """)
        result = self.db.execute(query)

        return [dict(row._mapping) for row in result]

    def get_platillos_by_id(self, id_detalle):
        query = text("""
            SELECT * 
            FROM vista_pedido_detalle_destino 
            WHERE id_detalle = :id_detalle 
            ORDER BY Fecha ASC
        """)
        result = self.db.execute(query, {"id_detalle": id_detalle})
        return [dict(row._mapping) for row in result]

    def cambiar_estatus(self, id_detalle: str, estado: str):
        try:

            self.db.execute(
                update(detalle_pedido)
                .where(detalle_pedido.c.id_detalle == id_detalle)
                .values(estado=estado)
            )

            self.db.commit()

            return {
                "message": f"estado del platillo cambiado a {estado}",
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar platillo: {e}")