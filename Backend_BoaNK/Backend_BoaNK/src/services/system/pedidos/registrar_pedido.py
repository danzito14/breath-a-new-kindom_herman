from datetime import date
from typing import List

from fastapi import Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db
from src.services.system.email.email_service import EmailService


class Producto(BaseModel):
    cant: int
    nombre: str
    subtotal: int

class CorreoResumen(BaseModel):
    direccion: str
    metodo_pago: str
    precio: float
    productos: List[Producto]

class RegistrarPedido_Service:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db


    def obtener_correo(self, id_usuario):
        stmt = self.db.execute(select(usuarios.c.Correo_electronico).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt
    
    def obtener_usuario(self, id_usuario):
        stmt = self.db.execute(select(usuarios.c.Nickname).where(usuarios.c.id_usuario == id_usuario)).scalar()
        return stmt


    def enviar_correo_recibo(self, id_usuario:str, data: CorreoResumen):
        try:
            corrreo_electronico = self.obtener_correo(id_usuario)
            nickname = self.obtener_usuario(id_usuario)
            service = EmailService()
            id_pedido = "123123123123123123123"
            asunto = f"Recibo de compra id: {id_pedido}"
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
              <h2>🧾 Resumen de tu pedido</h2>
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

