import uuid
import asyncio
from datetime import date, datetime
from typing import List, Optional

from fastapi import Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, delete, update, literal
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from src.db.model.carrito_model import carrito, detalle_carrito
from src.db.model.pedidos.pedido_temporal import pedido_temporal
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.platillo_model import platillo
from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db
from src.schemas.pedidos.pedido_schema import Pedido_Schema, Detalle_Pedido_Schema
from src.schemas.pedidos.pedidostemporal_schema import pedido_temporalSchema
from src.services.repositories.mesa_service import MesaService
from src.services.system.email.email_service import EmailService
from src.services.repositories.usuario_service import UsuarioService
from src.services.repositories.direcciones_usuario_service import Direcciones_usuarioService
from src.schemas.direcciones_usuario_schema import Direcciones_usuarioSchema

# 🔥 IMPORTAR EL GESTOR DE WEBSOCKET
from src.core.websocket_manager import manager


class Producto(BaseModel):
    cant: int
    nombre: str
    subtotal: int


class CorreoResumen(BaseModel):
    id_temporal: str
    direccion: Optional[str] = None
    metodo_pago: Optional[str] = None
    precio: float
    productos: List[Producto]
    id_pedido: Optional[str] = None


class RegistrarPedido_Service:
    def __init__(self, db: Session = Depends(get_db),
                 background_tasks: Optional[BackgroundTasks] = None):
        self.db = db
        self.background_tasks = background_tasks

    def pedido_main(self, id_usuario: str, nvl_usuario: str, data: CorreoResumen):
        id_temporal = data.id_temporal
        result = self.db.execute(
            select(pedido_temporal).where(pedido_temporal.c.id_temporal == id_temporal)
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Pedido temporal no encontrado")

        row_dict = dict(result._mapping)
        datos_temporal = pedido_temporalSchema(**row_dict)

        if nvl_usuario == '4':
            result_m = self.create_user_temporal(row_dict)
            var_id_usuario = result_m.get('id_usuario')
            id_direccion = self.create_direccion_temporal(var_id_usuario, row_dict)
            datos_temporal.id_direccion = id_direccion["id_direccion"]
            datos_temporal.id_usuario = var_id_usuario
            variable = self.create_pedido(var_id_usuario, datos_temporal)
            id_pedido_cabeza = variable.get("id_pedido")
        else:
            if not data.id_pedido:
                variable = self.create_pedido(id_usuario, datos_temporal)
                id_pedido_cabeza = variable.get("id_pedido")
            else:
                id_pedido_cabeza = data.id_pedido
                self.actualizar_pedido(id_pedido_cabeza, data.precio)

        array_ids_carrito = datos_temporal.datos_pedido
        platillos_info = self.create_pedido_detalle(id_pedido_cabeza, array_ids_carrito)

        self.delete_carritos(id_temporal, array_ids_carrito)

        # 🔥 NOTIFICAR VÍA WEBSOCKET A LOS COCINEROS
        if self.background_tasks:
            self.background_tasks.add_task(
                self._notificar_nuevo_pedido_async,
                id_pedido_cabeza,
                datos_temporal,
                platillos_info
            )

        if nvl_usuario == "1":
            self.enviar_correo_recibo(id_usuario, id_pedido_cabeza, data)

        return {"message": "Pedido registrado exitosamente", "id_pedido": id_pedido_cabeza}

    def create_pedido(self, id_usuario: str, data_temporal: pedido_temporalSchema):
        try:
            temporal_dict = data_temporal.dict(exclude_unset=True)
            pedido_cabeza_dict = Pedido_Schema(
                id_pedido=str(uuid.uuid4()),
                id_usuario=id_usuario,
                id_mesa=temporal_dict.get("id_mesa"),
                id_direccion=temporal_dict.get("id_direccion"),
                Fecha=datetime.today(),
                Estado='Pendiente',
                Tipo_pedido=(
                    'Local' if temporal_dict.get("id_mesa")
                    else 'Entrega' if temporal_dict.get("id_direccion")
                    else None
                ),
                total=temporal_dict.get("precio", 0)
            )

            id_mesa = temporal_dict.get("id_mesa")
            if id_mesa:
                self.ocupar_mesa(id_mesa)

            try:
                body_dict = pedido_cabeza_dict.dict(exclude_unset=True)
                stmt = insert(pedido).values(**body_dict)
                self.db.execute(stmt)
                self.db.commit()
                return {"message": "registro de pedido cabeza exitoso", "id_pedido": body_dict["id_pedido"]}
            except Exception as e:
                self.db.rollback()
                raise HTTPException(status_code=400, detail=f"Error al registrar el pedido: {e}")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al registrar el pedido: {e}")

    def actualizar_pedido(self, id_pedido: str, precio: float):
        try:
            stmt = (
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(total=pedido.c.total + literal(precio),Estado="Preparando")
            )
            self.db.execute(stmt)
            self.db.commit()
            print(f"Pedido {id_pedido} actualizado correctamente (+{precio}).")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al actualizar el pedido: {e}")

    def create_pedido_detalle(self, id_pedido: str, ids_carrito: List[str]):
        try:
            platillos_agregados = []

            for id_p in ids_carrito:
                query = select(detalle_carrito).where(detalle_carrito.c.id_detalle_carrito == id_p)
                result = self.db.execute(query).fetchone()

                id_platillo = result._mapping["id_platillo"]
                if id_platillo is None:
                    raise HTTPException(status_code=404, detail=f"No se encontró el platillo con id {id_platillo}")

                query2 = select(platillo).where(platillo.c.id_platillo == id_platillo)
                result2 = self.db.execute(query2).first()

                if result2 is None:
                    raise HTTPException(status_code=404, detail=f"No se encontró el platillo con id {id_platillo}")

                detalle_pedido_dict = Detalle_Pedido_Schema(
                    id_detalle=str(uuid.uuid4()),
                    id_pedido=id_pedido,
                    id_platillo=result._mapping["id_platillo"],
                    Precio_unitario=result._mapping["precio_unitario"],
                    tiempo_total=result2._mapping["tiempo_preparacion"],
                    estado='pendiente',
                    detalles_adicionales=result._mapping["detalles_adicionales"]
                )

                stmt = insert(detalle_pedido).values(**detalle_pedido_dict.dict(exclude_unset=True))
                self.db.execute(stmt)

                # 🔥 Recopilar info para notificación WebSocket
                platillos_agregados.append({
                    "id_detalle": detalle_pedido_dict.id_detalle,
                    "id_platillo": detalle_pedido_dict.id_platillo,
                    "nombre_platillo": result2._mapping.get("nombre", "Platillo"),
                    "tiempo_preparacion": detalle_pedido_dict.tiempo_total,
                    "precio_unitario": detalle_pedido_dict.Precio_unitario,
                    "detalles_adicionales": detalle_pedido_dict.detalles_adicionales
                })

            self.db.commit()
            return platillos_agregados

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al registrar el pedido detalle: {e}")

    # 🔥 MÉTODO PARA NOTIFICAR VÍA WEBSOCKET
    async def _notificar_nuevo_pedido_async(self, id_pedido: str, datos_temporal, platillos_info: List[dict]):
        """Notifica a cocina sobre nuevos platillos pendientes"""
        try:
            mensaje = {
                "tipo": "nuevo_pedido",
                "id_pedido": id_pedido,
                "tipo_pedido": "Local" if datos_temporal.id_mesa else "Entrega",
                "id_mesa": datos_temporal.id_mesa,
                "platillos": platillos_info,
                "timestamp": datetime.now().isoformat()
            }

            # Enviar notificación a todos los cocineros conectados
            await manager.broadcast_to_group(mensaje, "cocineros")
            await manager.broadcast_to_group(mensaje, "meseros")
            print(f"✅ Notificación WebSocket enviada a cocineros: {id_pedido}")

        except Exception as e:
            print(f"❌ Error al enviar notificación WebSocket: {e}")

    def delete_carritos(self, id_temporal, array_carrito: List[str]):
        try:
            for id_c in array_carrito:
                stmt = delete(detalle_carrito).where(detalle_carrito.c.id_detalle_carrito == id_c)
                result = self.db.execute(stmt)

            stmt_temproal = delete(pedido_temporal).where(pedido_temporal.c.id_temporal == id_temporal)
            result2 = self.db.execute(stmt_temproal)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se encontró el platillo a eliminar")

            return {"message": "Platillo eliminado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def ocupar_mesa(self, id_mesa: str):
        service_mesas = MesaService(self.db)
        data = {"Estado": "Ocupada"}
        service_mesas.update_mesa(id_mesa, data)

    def obtener_correo(self, id_usuario):
        stmt = self.db.execute(
            select(usuarios.c.Correo_electronico).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt

    def obtener_usuario(self, id_usuario):
        stmt = self.db.execute(select(usuarios.c.Nickname).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt

    def enviar_correo_recibo(self, id_usuario: str, id_pedido: str, data: CorreoResumen):
        try:
            corrreo_electronico = self.obtener_correo(id_usuario)
            nickname = self.obtener_usuario(id_usuario)
            service = EmailService()
            asunto = f"Restaurant Breath of a New Kingdom: Recibo de compra id: {id_pedido}"
            fecha = date.today()
            texto = f"""
            Gracias por su compra su Alteza {nickname}
            ID: Pedido:{id_pedido}, Fecha {fecha}, Restaurant Breath of a New Kingdom
            """

            productos_html = "".join([
                f"<li><strong>{p.cant}</strong> × {p.nombre} Subtotal: {p.subtotal}</li> " for p in data.productos
            ])

            html = f"""
            <div style="font-family: Arial; padding: 16px; border: 1px solid #ccc; border-radius: 8px;">
              <h2>🧾 Resumen de su orden su Majestad {nickname}</h2>
              <p><strong>Usuario:</strong> {nickname}</p>              
              <p><strong>Dirección:</strong> {data.direccion}</p>
              <p><strong>Método de pago:</strong> {data.metodo_pago}</p>
              <p><strong>Total:</strong> ${data.precio:.2f}</p>
              <h3>Productos:</h3>
              <ul>{productos_html}</ul>
              <p style="color: gray; font-size: 12px;">Gracias por tu compra su Majestad {nickname}</p>
            </div>
            """

            service.enviar_correo(corrreo_electronico, asunto, texto, html)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al enviar el correo: {e}")

    def create_user_temporal(self, result_dict: dict):
        id_usuario = str(uuid.uuid4())
        nickname = 'Usuario_generico_' + uuid.uuid4().hex[:4]
        service_user = UsuarioService(self.db)
        nombre_titular = result_dict.get("titular")

        try:
            service_user.create_user(
                id_usuario=id_usuario,
                id_nvl_usuario=8,
                Nickname=nickname,
                Contraseña='123456789#',
                Nombre=nombre_titular,
                Apellido='...',
                Correo_electronico='correo@example.com',
                Num_telefonico='1231231231',
                Ruta_imagen='...',
                estatus='True'
            )

            self.db.commit()
            return {
                "message": "Empleado registrado correctamente",
                "id_usuario": id_usuario
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"{str(e)}")

    def create_direccion_temporal(self, id_usuario: str, result_dict: dict):
        data_dict = Direcciones_usuarioSchema(
            id_usuario=id_usuario,
            alias="Temporal" + uuid.uuid4().hex[:4],
            Calle=",",
            No_ext=",",
            No_int=",",
            Colonia=",",
            CP=",",
            Ciudad=",",
            Municipio=",",
            Estado=",",
            instrucciones_add=result_dict.get("direccion"),
            temporal="1"
        )

        direcciones_service = Direcciones_usuarioService(self.db)
        res = direcciones_service.create_direcciones_usuario(data_dict)
        self.db.commit()
        return {"id_direccion": res.get("id_direccion")}