from datetime import datetime

from sqlalchemy import Table, Column, CHAR, Enum, String, Integer, DECIMAL, Boolean, DATETIME, JSON
from src.core.db_credentials import meta_data

pedido_temporal = Table ("pedido_temporal", meta_data,
                Column("id_temporal",CHAR(36),primary_key=True),
                Column("id_usuario",CHAR(36), nullable=False),
                Column("datos_pedido", JSON,nullable=False),
                Column("fecha_creacion", DATETIME, nullable=False),
                Column("pagado",Boolean, default=False, nullable=False),
                Column("precio", DECIMAL(8,2), nullable=False),
                Column("lista_producto", JSON, nullable=False),
                Column("metodo_pago",Enum('Efectivo','Tarjeta', name="metodo_pago"), nullable=True),
                Column("id_tarjeta",CHAR(36), nullable=True),
                Column("direccion",CHAR(200), nullable=True),
                Column("id_mesa", CHAR(36), nullable=True)
       )