from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import Table, Column, String, Boolean, Integer, CHAR
from src.core.db_credentials import meta_data

carrito = Table("carrito", meta_data,
                Column("id_carrito", CHAR(36), primary_key=True),
                Column("id_usuario", CHAR(36), nullable=False)
                )

detalle_carrito = Table ("detalle_carrito", meta_data,
                         Column("id_detalle_carrito", CHAR(36), primary_key=True),
                        Column("id_carrito", CHAR(36), nullable=False),
                        Column("id_platillo", CHAR(36), nullable=False),
                        Column("precio_unitario", DECIMAL(8,2), nullable=False),
                        Column("detalles_adicionales",String(100), nullable=False)
                         )