from sqlalchemy import Table, Column, Integer, Boolean, String, Enum, DATETIME
from sqlalchemy.dialects.mysql import CHAR

from src.core.db_credentials import meta_data

repartidores = Table ("repartidores", meta_data,
            Column("id_repartidor", CHAR(36), primary_key=True),
    Column ("id_usuario", CHAR(36), nullable=False),
    Column ("activo", Boolean, nullable=False),
    Column( "en_ruta", Boolean, nullable=False),
    Column("pedidos_asignados",Integer, nullable=False),
    Column("estado", Enum('En local', 'Repartiendo', name="estado_enum"), nullable=False),
    Column("id_pedido",CHAR(36), nullable=True)
)