from sqlalchemy import Table, Column, CHAR, Enum, String, Integer, DECIMAL, Boolean, DATETIME
from src.core.db_credentials import meta_data

pedido = Table("pedido", meta_data,
               Column("id_pedido", CHAR(36), primary_key=True),
                Column("id_usuario",CHAR(36), nullable=False),
                Column("id_mesa",CHAR(36), nullable=True),
                Column("id_auto",CHAR(36), nullable=True),
                Column("total", Integer, nullable=False),
                Column("Fecha", DATETIME, nullable=False),
                Column("Estado", Enum('Pendiente','Preparando','Listo','En camino','Entregado','Pagada','Cancelado', name="Estado_num"), nullable=False),
                Column("Tipo_pedido",Enum('Entrega','Local'), nullable=False),
               Column("id_direccion", CHAR(36), nullable=False)
               )

detalle_pedido = Table("detalle_pedido", meta_data,
                    Column("id_detalle", CHAR(36),primary_key=True),
                Column("id_pedido",CHAR(36), nullable=False),
                Column("id_platillo",CHAR(36), nullable=False),
                Column("Precio_unitario",DECIMAL(10,2), nullable=False),
                Column("tiempo_total",Integer, nullable=False),
                Column("estado", Enum('pendiente','cocinando','listo', name="estado_enum"), nullable=False),
                Column("detalles_adicionales",String(100), nullable=False)
                       )