import uuid
from datetime import datetime
from operator import not_
from typing import List, Optional

from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, delete, update, literal, func, desc, case, text, and_
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.db.model.direcciones_usuario_model import direcciones_usuario
from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.platillo_model import platillo
from src.db.model.usuario_model import usuarios
from src.db.model.pedidos.repartidores_model import  repartidores, lista_repartidores

from src.services.system.repartidores.repartidores_service import RepartidorService

# 🔥 IMPORTAR EL GESTOR DE WEBSOCKET
from src.core.websocket_manager import manager

""""
    Aqui se la info de los pedidos ya sea para cocinero, mesero, usuario etc
"""

class PedidoService_Gets:
    def __init__(self, db: Session = Depends(get_db),
                 background_tasks: Optional[BackgroundTasks] = None):
        self.db = db
        self.background_tasks = background_tasks

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
                    pedido.c.Estado.notin_([ "Cancelado", "Pagada"]),
                    detalle_pedido.c.estado.notin_(["cancelado"])
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

    def get_pedidos_by_id_for_repartidor(self, id_pedido: str):
        """
        Obtiene los datos de un pedido filtrado por el id de un pedido,
        normalmente usado para cuando un repartidor ya tiene pedido asignado y recarga la pagina
        """
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
                lista_repartidores.c.estado_pedido.label("estado_lista"),
                lista_repartidores.c.fecha_asignado,
                direccion_label
            )
            .join(lista_repartidores, lista_repartidores.c.id_pedido == pedido.c.id_pedido)
            .join(usuarios, usuarios.c.id_usuario == pedido.c.id_usuario)
            .join(detalle_pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
            .join(platillo, platillo.c.id_platillo == detalle_pedido.c.id_platillo)
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .where(
                and_(
                    pedido.c.id_pedido == id_pedido,
                    lista_repartidores.c.estado_pedido.in_(["pendiente", "en_camino"]),
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
                    "estado_lista": r.estado_lista,
                    "fecha_asignado": r.fecha_asignado,
                    "tipo_pedido": r.Tipo_pedido,
                    "id_usuario": r.id_usuario,
                    "nombre_completo": r.nombre_completo,
                    "total": r.total,
                    "id_direccion": r.id_direccion,
                    "direccion_completa": r.direccion_completa,
                    "platillos": []
                }

            pedidos_dict[id_pedido]["platillos"].append({
                "id_detalle": r.id_detalle,
                "nombre_platillo": r.Nombre_platillo,
                "estado_detalle": r.estado_detalle,
                "detalles_adicionales": r.detalles_adicionales
            })

        return list(pedidos_dict.values())



    def get_pedidos_repartidor(self, id_usuario: str):
        """
        Obtiene los pedidos asignados a un repartidor específico
        filtrando por id_usuario en lista_repartidores
        """
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
                pedido.c.forma_pago,
                pedido.c.id_direccion,
                detalle_pedido.c.id_detalle,
                detalle_pedido.c.estado.label("estado_detalle"),
                detalle_pedido.c.detalles_adicionales,
                platillo.c.Nombre_platillo,
                lista_repartidores.c.estado_pedido.label("estado_lista"),
                lista_repartidores.c.fecha_asignado,
                direccion_label
            )
            .join(lista_repartidores, lista_repartidores.c.id_pedido == pedido.c.id_pedido)
            .join(usuarios, usuarios.c.id_usuario == pedido.c.id_usuario)
            .join(detalle_pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
            .join(platillo, platillo.c.id_platillo == detalle_pedido.c.id_platillo)
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .where(
                and_(
                    lista_repartidores.c.id_usuario == id_usuario,
                    lista_repartidores.c.estado_pedido.in_(["pendiente", "en_camino"]),
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
                    "estado_lista": r.estado_lista,
                    "fecha_asignado": r.fecha_asignado,
                    "tipo_pedido": r.Tipo_pedido,
                    "forma_pago": r.forma_pago,
                    "id_usuario": r.id_usuario,
                    "nombre_completo": r.nombre_completo,
                    "total": r.total,
                    "id_direccion": r.id_direccion,
                    "direccion_completa": r.direccion_completa,
                    "platillos": []
                }

            pedidos_dict[id_pedido]["platillos"].append({
                "id_detalle": r.id_detalle,
                "nombre_platillo": r.Nombre_platillo,
                "estado_detalle": r.estado_detalle,
                "detalles_adicionales": r.detalles_adicionales
            })

        return list(pedidos_dict.values())

    def get_pedidos_usuario(self, id_usuario: str):
        """
        Obtiene todos los pedidos realizados por un usuario normal
        (NO repartidor), incluyendo sus platillos y dirección.
        """

        direccion_label = func.concat(
            direcciones_usuario.c.Calle, " ",
            direcciones_usuario.c.No_ext, ", ",
            direcciones_usuario.c.No_int, ", ",
            direcciones_usuario.c.Colonia, ", ",
            direcciones_usuario.c.Ciudad, ", ",
            direcciones_usuario.c.Estado, ", CP ",
            direcciones_usuario.c.CP, " ",
            direcciones_usuario.c.instrucciones_add
        ).label("direccion_completa")

        query = (
            select(
                pedido.c.id_pedido,
                pedido.c.Fecha,
                pedido.c.Estado.label("estado_pedido"),
                pedido.c.Tipo_pedido,
                pedido.c.total,
                pedido.c.forma_pago,
                pedido.c.id_direccion,
                detalle_pedido.c.id_detalle,
                detalle_pedido.c.estado.label("estado_detalle"),
                detalle_pedido.c.detalles_adicionales,
                platillo.c.Nombre_platillo,
                direccion_label
            )
            .join(detalle_pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
            .join(platillo, platillo.c.id_platillo == detalle_pedido.c.id_platillo)
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .where(
                pedido.c.id_usuario == id_usuario
            )
            .order_by(desc(pedido.c.Fecha))
        )

        rows = self.db.execute(query).all()

        # Agrupar por pedido
        pedidos_dict = {}

        for r in rows:
            id_pedido = r.id_pedido

            if id_pedido not in pedidos_dict:
                pedidos_dict[id_pedido] = {
                    "id_pedido": r.id_pedido,
                    "fecha": r.Fecha,
                    "estado_pedido": r.estado_pedido,
                    "tipo_pedido": r.Tipo_pedido,
                    "forma_pago": r.forma_pago,
                    "total": r.total,
                    "id_direccion": r.id_direccion,
                    "direccion_completa": r.direccion_completa,
                    "platillos": []
                }

            pedidos_dict[id_pedido]["platillos"].append({
                "id_detalle": r.id_detalle,
                "nombre_platillo": r.Nombre_platillo,
                "estado_detalle": r.estado_detalle,
                "detalles_adicionales": r.detalles_adicionales
            })

        return list(pedidos_dict.values())

    def cancelar_platillo(self, id_detalle: str, id_pedido: str, id_mesa: Optional[str] = None):
        try:
            cancelar_pedido = False

            # 1️⃣ Obtener precio del detalle
            precio_result = self.db.execute(
                select(detalle_pedido.c.Precio_unitario)
                .where(detalle_pedido.c.id_detalle == id_detalle)
            ).first()

            if not precio_result:
                raise HTTPException(status_code=404, detail="Platillo no encontrado")

            precio_platillo = precio_result[0]

            # 2️⃣ Cambiar estado a cancelado
            self.db.execute(
                update(detalle_pedido)
                .where(detalle_pedido.c.id_detalle == id_detalle)
                .values(estado="cancelado")
            )

            # 3️⃣ Restar del total siempre que no se cancele completamente
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(total=pedido.c.total - precio_platillo)
            )

            tipo_pedido = self.db.execute(
                select(pedido.c.Tipo_pedido)
                .where(pedido.c.id_pedido == id_pedido)
            ).scalar()

            self.db.commit()

            # 4️⃣ Recalcular el estado completo del pedido
            nuevo_estado = self._actualizar_estado_pedido(id_pedido, id_mesa)

            if nuevo_estado == "Cancelado":
                # Se canceló TODO el pedido → enviar notificacion de PEDIDO cancelado
                self.background_tasks.add_task(
                    self._notificar_pedido_cancelado,
                    id_pedido, tipo_pedido
                )
            else:
                # Solo se canceló un platillo → enviar notificacion de PLATILLO cancelado
                self.background_tasks.add_task(
                    self._notificar_platillo_cancelado,
                    id_detalle, tipo_pedido
                )

            return {
                "message": "Platillo cancelado"
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar platillo: {e}")

    def cancelar_pedido(self, id_pedido: str, id_mesa: str, id_repartidor: Optional[str]):
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

            tipo_pedido = self.db.execute(
                select(pedido.c.Tipo_pedido)
                .where(pedido.c.id_pedido == id_pedido)
            ).scalar()

            if tipo_pedido == 'Entrega':
                serviceRepartidores = RepartidorService(self.db)
                serviceRepartidores.finalizar_pedido(id_pedido, id_repartidor)

            self.db.commit()

            self.background_tasks.add_task(
                self._notificar_pedido_cancelado,
                id_pedido, tipo_pedido
            )



            return {"message": "Pedido cancelado correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cancelar pedido: {e}")



    def _actualizar_estado_pedido(self, id_pedido: str, id_mesa: Optional[str] = None):
        # Obtener estados de todos los platillos del pedido
        estados = self.db.execute(
            select(detalle_pedido.c.estado)
            .where(detalle_pedido.c.id_pedido == id_pedido)
        ).fetchall()

        if not estados:
            return  # No hay platillos

        estados = [e[0].lower() for e in estados]

        # Si TODOS están cancelados → cancelar pedido completo
        if all(e == "cancelado" for e in estados):
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(Estado="Cancelado", total=0)
            )
            if id_mesa:
                self.db.execute(
                    update(mesa)
                    .where(mesa.c.id_mesa == id_mesa)
                    .values(Estado="Libre")
                )
            self.db.commit()
            return "Cancelado"

        # Si hay pendiente o cocinando → sigue preparando
        if any(e in ("pendiente", "cocinando") for e in estados):
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(Estado="Preparando")
            )
            self.db.commit()
            return "Preparando"

        # Si hay al menos un "listo" → pedido listo
        if any(e == "listo" for e in estados):
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(Estado="Listo")
            )
            self.db.commit()
            return "Listo"

        # Si todos son "servido" → pedido entregado
        if all(e == "servido" for e in estados if e != "cancelado"):
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(Estado="Entregado")
            )
            self.db.commit()
            return "Entregado"

        return None
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
                  SELECT * FROM vista_pedido_detalle_destino where estado = 'listo' and Tipo_pedido = 'Local' order by Fecha ASC
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
            # Obtener información del platillo antes de actualizar
            query = select(
                detalle_pedido.c.id_detalle,
                detalle_pedido.c.id_pedido,
                detalle_pedido.c.id_platillo,
                detalle_pedido.c.estado,
                platillo.c.Nombre_platillo,
                pedido.c.id_mesa,
                pedido.c.Tipo_pedido,
                mesa.c.Nombre_mesa
            ).select_from(
                detalle_pedido
                .join(platillo, detalle_pedido.c.id_platillo == platillo.c.id_platillo)
                .join(pedido, detalle_pedido.c.id_pedido == pedido.c.id_pedido)
                .outerjoin(mesa, pedido.c.id_mesa == mesa.c.id_mesa)
            ).where(detalle_pedido.c.id_detalle == id_detalle)

            resultado = self.db.execute(query).first()

            if not resultado:
                raise HTTPException(status_code=404, detail="Platillo no encontrado")

            id_pedido = resultado.id_pedido
            id_mesa = resultado.id_mesa
            tipo_pedido = resultado.Tipo_pedido

            # Actualizar estado del platillo
            self.db.execute(
                update(detalle_pedido)
                .where(detalle_pedido.c.id_detalle == id_detalle)
                .values(estado=estado)
            )

            # Commit del cambio del platillo
            self.db.commit()

            # ⭐ Recalcular estado del pedido
            nuevo_estado = self._actualizar_estado_pedido(id_pedido, id_mesa)

            # 🚀 SI EL PEDIDO COMPLETO ESTÁ LISTO Y ES PARA ENTREGA → ASIGNAR REPARTIDOR
            pedido_asignado = False
            if nuevo_estado == "Listo" and tipo_pedido == "Entrega":
                if self.background_tasks:
                    # Asignar con IA usando el servicio de repartidores
                    self.background_tasks.add_task(
                        self._asignar_pedido_automaticamente,
                        id_pedido
                    )
                    pedido_asignado = True

            # 🔥 Notificar si el platillo se marcó como listo
            if estado == 'listo':
                if self.background_tasks:
                    self.background_tasks.add_task(
                        self._notificar_platillo_listo,
                        resultado
                    )
                else:
                    import asyncio
                    asyncio.create_task(self._notificar_platillo_listo(resultado))

            return {
                "message": f"Estado del platillo cambiado a {estado}",
                "id_detalle": id_detalle,
                "estado": estado,
                "nuevo_estado_pedido": nuevo_estado,
                "tipo_pedido": tipo_pedido,
                "asignacion_automatica": pedido_asignado
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al cambiar estado: {e}")

    # 🔥 MÉTODO PARA NOTIFICAR A MESEROS VÍA WEBSOCKET
    async def _notificar_platillo_listo(self, platillo_info):
        """Notifica a los meseros que un platillo está listo"""
        try:
            mensaje = {
                "tipo": "platillo_listo",
                "id_detalle": platillo_info.id_detalle,
                "id_pedido": platillo_info.id_pedido,
                "nombre_platillo": platillo_info.Nombre_platillo,
                "tipo_pedido": platillo_info.Tipo_pedido,
                "id_mesa": platillo_info.id_mesa,
                "nombre_mesa": platillo_info.Nombre_mesa,
                "timestamp": datetime.now().isoformat()
            }

            # 🔥 Enviar notificación a TODOS los meseros conectados
            await manager.broadcast_to_group(mensaje, "meseros")
            await manager.broadcast_to_group(mensaje, "cocineros")

            print(f"✅ Notificación enviada a meseros: Platillo {platillo_info.nombre_platillo} listo")

        except Exception as e:
            print(f"❌ Error al enviar notificación WebSocket a meseros: {e}")

    # 🔥 OPCIONAL: Método para notificar también a cocineros cuando se cancela
    async def _notificar_platillo_cancelado(self, id_pedido, tipo_pedido:str):
        """Notifica cuando un platillo es cancelado"""
        try:
            mensaje = {
                "tipo": "platillo_cancelado",
                "id_detalle":id_pedido
            }

            # Notificar tanto a meseros como a cocineros
            if tipo_pedido == 'Local':
                await manager.broadcast_to_group(mensaje, "meseros")
            if tipo_pedido == 'Entrega':
                await manager.broadcast_to_group(mensaje, "repartidor")

            await manager.broadcast_to_group(mensaje, "cocineros")
            print(f"✅ Notificación de cancelación enviada: {id_pedido}")

        except Exception as e:
            print(f"❌ Error al enviar notificación de cancelación: {e}")

    async def _notificar_pedido_cancelado(self, id_pedido, tipo_pedido:str):
        """Notifica cuando un platillo es cancelado"""
        try:
            mensaje = {
                "tipo": "pedido_cancelado",
                "id_pedido": id_pedido
            }

            # Notificar tanto a meseros como a cocineros
            if tipo_pedido == 'Local':
                await manager.broadcast_to_group(mensaje, "meseros")
            if tipo_pedido == 'Entrega':
                await manager.broadcast_to_group(mensaje, "repartidor")

            await manager.broadcast_to_group(mensaje, "cocineros")
            print(f"✅ Notificación de cancelación enviada: {id_pedido}")

        except Exception as e:
            print(f"❌ Error al enviar notificación de cancelación: {e}")

    async def _asignar_pedido_automaticamente(self, id_pedido: str):
        """
        Se ejecuta automáticamente cuando un pedido de entrega está listo.
        Usa IA (Gemini) para asignar al mejor repartidor.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)

            repartidor_service = RepartidorService(self.db)
            resultado = await repartidor_service.asignar_pedido_con_ia(id_pedido)

            logger.info(f"✅ Pedido {id_pedido} asignado automáticamente")
            logger.info(f"   Repartidor: {resultado['id_repartidor']}")
            logger.info(f"   Razón: {resultado['razon_asignacion']}")

            # Notificar a cajeros/administradores sobre la asignación
            mensaje = {
                "tipo": "pedido_asignado_repartidor",
                "id_pedido": id_pedido,
                "id_repartidor": resultado['id_repartidor'],
                "razon": resultado['razon_asignacion'],
                "prioridad": resultado.get('prioridad', 'media'),
                "timestamp": datetime.now().isoformat()
            }

            # Notificar a admin y meseros
            await manager.broadcast_to_group(mensaje, "repartidor")
#            await manager.broadcast_to_group(mensaje, "meseros")

            logger.info("📡 Notificaciones de asignación enviadas")

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error al asignar pedido automáticamente: {e}")
            #

    """
    ###########################################################################################################
    """
    def cambiar_estado_pedido(self, id_pedido:str, Estado:str):
        self.db.execute(
            update(pedido)
            .where(pedido.c.id_pedido == id_pedido)
            .values(Estado = Estado)
        )