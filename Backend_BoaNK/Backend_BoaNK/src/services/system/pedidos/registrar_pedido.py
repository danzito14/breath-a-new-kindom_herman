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
    def __init__(self, db: Session = Depends(get_db), ws_manager=None,
                 background_tasks: Optional[BackgroundTasks] = None):
        self.db = db
        self.ws_manager = ws_manager
        self.background_tasks = background_tasks
    """
        Por si me pierdo, lo que voy a hacer es tomar los valores de temporal pedido, y los voy a registrar
        en pedido y detalle pedido, despues voy a borrar los platillos del carrito y vaciar la tupla de temporal pedido y por ultimo enviar el correo
        
        Orden del flujo
        obtener el id_temporal de data  LISTO> buscar ese id_temporal en la tabla temporal pedido LISTO > sacar los datos necesarios para el crear la cabeza del platillo LISTO
            sacar los ids_carrito de la columna datos_pedido de la tabla pedidotemporal
            > registrar esos productos en detalle pedido > eliminar los productos del carrito > vaciar/elimnar la tupla del pedido_temporal > enviar correo
        
    """
    def pedido_main(self, id_usuario:str, nvl_usuario:str, data: CorreoResumen):
       # sacamos el id temporal
        id_temporal = data.id_temporal
        # obtenemos todos los datos de la tupla

        result = self.db.execute(
            select(pedido_temporal).where(pedido_temporal.c.id_temporal == id_temporal)
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Pedido temporal no encontrado")

        row_dict = dict(result._mapping)
        datos_temporal = pedido_temporalSchema(**row_dict)

        if nvl_usuario == '4':
            """
                Si es nvl 4 eso quiere decir que es el cajero que esta haciendo un pedido aun cliente común por lo que se le tiene que hacer una
                cuenta temporal y una direccion temporal que al cancelar o entregar el pedido se tiene que eliminar
            """
            result_m = self.create_user_temporal(row_dict)
            var_id_usuario = result_m.get('id_usuario')

            id_direccion = self.create_direccion_temporal(var_id_usuario, row_dict)

            datos_temporal.id_direccion = id_direccion["id_direccion"]
            datos_temporal.id_usuario = var_id_usuario

            variable = self.create_pedido(var_id_usuario, datos_temporal)
            id_pedido_cabeza = variable.get("id_pedido")
            # 🔥 CORREGIDO: Usar background_tasks en lugar de asyncio.create_task
            if self.ws_manager and self.background_tasks:
                self.background_tasks.add_task(
                    self._notificar_nuevo_pedido,
                    id_pedido_cabeza,
                    datos_temporal
                )
        else:

            if not data.id_pedido:
                variable = self.create_pedido(id_usuario, datos_temporal)
                id_pedido_cabeza = variable.get("id_pedido")


                # 🔥 CORREGIDO: Usar background_tasks en lugar de asyncio.create_task
                if self.ws_manager and self.background_tasks:
                    self.background_tasks.add_task(
                        self._notificar_nuevo_pedido,
                        id_pedido_cabeza,
                        datos_temporal
                    )

            else:
                id_pedido_cabeza = data.id_pedido
                self.actualizar_pedido(id_pedido_cabeza, data.precio)

                # 🔥 CORREGIDO: Usar background_tasks
                if self.ws_manager and self.background_tasks:
                    self.background_tasks.add_task(
                        self._notificar_actualizacion_pedido,
                        id_pedido_cabeza
                    )


       #sacamos el id o ids de datos_pedido que contiene ["id1","id2",...]
        array_ids_carrito = datos_temporal.datos_pedido
        self.create_pedido_detalle(id_pedido_cabeza, array_ids_carrito)

        #una vez registrado todo borramos del carrito los productos comprados
        self.delete_carritos(id_temporal, array_ids_carrito)
        print(nvl_usuario)
        # y enviamos el correo
        if nvl_usuario == "1":
            self.enviar_correo_recibo(id_usuario,id_pedido_cabeza, data)

    def create_pedido(self, id_usuario:str, data_temporal: pedido_temporalSchema):
        try:
            #lo volvemos un diccionario
            temporal_dict = data_temporal.dict(exclude_unset=True)

        #vamos a armar el diccionario para registrar en la tabla pedido
            #inicializamos el dict con los datos del schema
            pedido_cabeza_dict = Pedido_Schema(
                id_pedido=str(uuid.uuid4()),
                id_usuario=id_usuario,
                id_mesa=temporal_dict.get("id_mesa"),
                id_direccion=temporal_dict.get("id_direccion"),
                Fecha=datetime.today(),
                Estado='Pendiente',  # Enum "pendiente"
                Tipo_pedido=(
                    'Local' if temporal_dict.get("id_mesa")
                    else 'Entrega' if temporal_dict.get("id_direccion")
                    else None
                ),
                total=temporal_dict.get("precio", 0)
            )


            # si existe el id_mesa la vamos a ocupoar
            id_mesa = temporal_dict.get("id_mesa")
            self.ocupar_mesa(id_mesa)

            #una vez creado vamos a insertarlo
            try:
                body_dict = pedido_cabeza_dict.dict(exclude_unset=True)
                stmt = insert(pedido).values(**body_dict)
                self.db.execute(stmt)
                self.db.commit()
                #el return donde devolvemos el id_pedido para ingresar los platillos a detalle pedido
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
                .values(total=pedido.c.total + literal(precio))
            )
            self.db.execute(stmt)
            self.db.commit()
            print(f"Pedido {id_pedido} actualizado correctamente (+{precio}).")

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al actualizar el pedido: {e}")

    """
        Aqui vamos a enviarle ya sea 1 id o varios ids carrito para que saque los datos y los registre automaticamente en la 
        tabla detalle_pedido 
    """
    def create_pedido_detalle(self, id_pedido: str, ids_carrito: List[str]):
        try:
            platillos_agregados = []

            for id_p in ids_carrito:
                # 1️⃣ Obtenemos los datos del carrito
                query = select(detalle_carrito).where(detalle_carrito.c.id_detalle_carrito == id_p)
                result = self.db.execute(query).fetchone()

                # 2️⃣ Obtenemos el platillo relacionado
                id_platillo = result._mapping["id_platillo"]
                if id_platillo is None:
                    raise HTTPException(status_code=404, detail=f"No se encontró el platillo con id {id_platillo}")

                query2 = select(platillo).where(platillo.c.id_platillo == id_platillo)
                result2 = self.db.execute(query2).first()

                if result2 is None:
                    raise HTTPException(status_code=404, detail=f"No se encontró el platillo con id {id_platillo}")

                # 3️⃣ Creamos el detalle del pedido
                detalle_pedido_dict = Detalle_Pedido_Schema(
                    id_detalle=str(uuid.uuid4()),
                    id_pedido=id_pedido,
                    id_platillo=result._mapping["id_platillo"],
                    Precio_unitario=result._mapping["precio_unitario"],
                    tiempo_total=result2._mapping["tiempo_preparacion"],
                    estado='pendiente',
                    detalles_adicionales=result._mapping["detalles_adicionales"]
                )

                # 4️⃣ Insertamos el detalle
                stmt = insert(detalle_pedido).values(**detalle_pedido_dict.dict(exclude_unset=True))
                self.db.execute(stmt)

                # 🔥 NUEVO: Recopilar info para notificación
                platillos_agregados.append({
                    "id_detalle": detalle_pedido_dict.id_detalle,
                    "id_platillo": detalle_pedido_dict.id_platillo,
                    "nombre_platillo": result2._mapping.get("nombre", "Platillo"),
                    "tiempo_preparacion": detalle_pedido_dict.tiempo_total
                })

            # 5️⃣ Confirmamos la transacción
            self.db.commit()

            # 🔥 CORREGIDO: Notificar a cocina usando background_tasks
            if self.ws_manager and self.background_tasks and platillos_agregados:
                self.background_tasks.add_task(
                    self._notificar_cocina_platillos,
                    id_pedido,
                    platillos_agregados
                )

            return {"message": "Detalle de pedido registrado correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al registrar el pedido detalle: {e}")

        # 🔥 NUEVO: Métodos asíncronos para WebSocket

    async def _notificar_nuevo_pedido(self, id_pedido: str, datos_temporal):
        """Notifica a cocina y meseros sobre nuevo pedido"""
        mensaje = {
            "tipo": "nuevo_pedido",
            "id_pedido": id_pedido,
            "tipo_pedido": "Local" if datos_temporal.id_mesa else "Entrega",
            "id_mesa": datos_temporal.id_mesa,
            "timestamp": datetime.now().isoformat()
        }

        # Notificar a cocina
        await self.ws_manager.send_to_role("cocina", mensaje)

        # Notificar a meseros si es pedido local
        if datos_temporal.id_mesa:
            await self.ws_manager.send_to_role("meseros", mensaje)

    async def _notificar_actualizacion_pedido(self, id_pedido: str):
        """Notifica actualización de pedido existente"""
        mensaje = {
            "tipo": "actualizacion_pedido",
            "id_pedido": id_pedido,
            "timestamp": datetime.now().isoformat()
        }
        await self.ws_manager.send_to_role("cocina", mensaje)
        await self.ws_manager.send_to_role("meseros", mensaje)

    async def _notificar_cocina_platillos(self, id_pedido: str, platillos: List[dict]):
        """Notifica a cocina los platillos que deben preparar"""
        mensaje = {
            "tipo": "nuevos_platillos",
            "id_pedido": id_pedido,
            "platillos": platillos,
            "cantidad": len(platillos),
            "timestamp": datetime.now().isoformat()
        }
        await self.ws_manager.send_to_role("cocina", mensaje)





    def delete_carritos(self,id_temporal, array_carrito: List[str]):
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



    def ocupar_mesa(self, id_mesa:str):
        service_mesas = MesaService(self.db)
        data= {
         "Estado": "Ocupada"
        }
        service_mesas.update_mesa(id_mesa,data)

    """
    ################################################################################################################
    """

    def obtener_correo(self, id_usuario):
        stmt = self.db.execute(select(usuarios.c.Correo_electronico).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt
    
    def obtener_usuario(self, id_usuario):
        stmt = self.db.execute(select(usuarios.c.Nickname).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt


    def enviar_correo_recibo(self, id_usuario:str, id_pedido:str, data: CorreoResumen):
        try:
            corrreo_electronico = self.obtener_correo(id_usuario)
            nickname = self.obtener_usuario(id_usuario)
            service = EmailService()
            id_pedido = id_pedido
            asunto = f"Restaruant Breath of a New Kindom: Recibo de compra id: {id_pedido}"
            fecha= date.today()
            texto = f"""
            Gracias por su compra su Alteza {nickname}
            ID: Pedido:{id_pedido}, Fecha  {fecha}, Restaurant Breath of a New Kindom
            """

            # Construir HTML con estilo
            productos_html = "".join([
                f"<li><strong>{p.cant}</strong> × {p.nombre} Subotal: {p.subtotal}</li> " for p in data.productos
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


            service.enviar_correo(corrreo_electronico,asunto, texto, html)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al enviar el correo: {e}")




    """
    ################################################################################################################
    Temporales
    ################################################################################################################
    """
    def create_user_temporal(self, result_dict: dict):
        id_usuario = str(uuid.uuid4())
        nickname = 'Usuario_generico_'+uuid.uuid4().hex[:4]
        service_user = UsuarioService(self.db)
        nombre_titular = result_dict.get("titular")


        try:
            # Crear usuario
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
            raise HTTPException(status_code=400, detail=f"{str(e)} giragira anatarite")


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