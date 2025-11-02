import uuid
from datetime import date
from typing import List

from fastapi import Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select, delete
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
from src.services.system.email.email_service import EmailService


class Producto(BaseModel):
    cant: int
    nombre: str
    subtotal: int

class CorreoResumen(BaseModel):
    id_temporal: str
    direccion: str
    metodo_pago: str
    precio: float
    productos: List[Producto]

class RegistrarPedido_Service:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    """
        Por si me pierdo, lo que voy a hacer es tomar los valores de temporal pedido, y los voy a registrar
        en pedido y detalle pedido, despues voy a borrar los platillos del carrito y vaciar la tupla de temporal pedido y por ultimo enviar el correo
        
        Orden del flujo
        obtener el id_temporal de data  LISTO> buscar ese id_temporal en la tabla temporal pedido LISTO > sacar los datos necesarios para el crear la cabeza del platillo LISTO
            sacar los ids_carrito de la columna datos_pedido de la tabla pedidotemporal
            > registrar esos productos en detalle pedido > eliminar los productos del carrito > vaciar/elimnar la tupla del pedido_temporal > enviar correo
        
    """
    def pedido_main(self, id_usuario:str, data: CorreoResumen):
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

    #asi es no se me ocurrio mejor nombre para el diccionario que retorna
        variable = self.create_pedido(id_usuario, datos_temporal)

       #sacamos el id_pedido para registrar despues los productos en pedido detalle
        id_pedido_cabeza = variable.get("id_pedido")

       #sacamos el id o ids de datos_pedido que contiene ["id1","id2",...]
        array_ids_carrito = datos_temporal.datos_pedido
        self.create_pedido_detalle(id_pedido_cabeza, array_ids_carrito)

        #una vez registrado todo borramos del carrito los productos comprados
        self.delete_carritos(id_temporal, array_ids_carrito)

        # y enviamos el correo
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
                Fecha=date.today(),
                Estado='Pendiente',  # Enum "pendiente"
                Tipo_pedido=(
                    'Local' if temporal_dict.get("id_mesa")
                    else 'Entrega' if temporal_dict.get("id_direccion")
                    else None
                ),
                total=temporal_dict.get("precio", 0)
            )

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


    """
        Aqui vamos a enviarle ya sea 1 id o varios ids carrito para que saque los datos y los registre automaticamente en la 
        tabla detalle_pedido 
    """

    def create_pedido_detalle(self, id_pedido: str, ids_carrito: List[str]):
        try:
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

            # 5️⃣ Confirmamos la transacción
            self.db.commit()
            return {"message": "Detalle de pedido registrado correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al registrar el pedido detalle: {e}")


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

