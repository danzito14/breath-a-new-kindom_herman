
from sqlalchemy import Table, Column, CHAR, Enum, String, Integer, DECIMAL, Boolean, DATETIME, ForeignKey
from src.core.db_credentials import meta_data

pago = Table ("pago", meta_data,
Column("id_pago",CHAR(36),primary_key=True),
Column("id_pedido",CHAR(36), nullable=False),
Column("monto",DECIMAL(10,2), nullable=False),
Column("metodo_pago",String(30), nullable=False),
Column("referencia_pago", String(100), nullable=False),
Column("estado_pago", Enum('Exitoso','Pendiente','Fallido', name="estado_enum"), nullable=False),
Column("fecha_pago",DATETIME, nullable=False),
Column("pagado_por",CHAR(36), nullable=False)

              )