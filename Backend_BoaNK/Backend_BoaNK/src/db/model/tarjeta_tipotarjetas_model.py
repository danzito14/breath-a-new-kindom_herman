from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Table, Column, String, Integer, ForeignKey, Boolean
from src.core.db_credentials import meta_data

tarjetas_pago = Table(
    "tarjetas_pago",
    meta_data,
    Column("id_tarjeta", CHAR(36), primary_key=True),
    Column("id_usuario", CHAR(36), nullable=False),
    Column("titular", String(100), nullable=False),
    Column("num_tarjeta", String(19), nullable=False),
    Column("id_tipo_tarjeta", Integer, ForeignKey("tipos_tarjeta.id_tipo_tarjeta"), nullable=False),
    Column("mes_exp", CHAR(2), nullable=False),
    Column("anio_exp", CHAR(4), nullable=False),
    Column("predeterminada", Boolean, nullable=False, default=False)
)

tipos_tarjeta = Table(
    "tipos_tarjeta",
    meta_data,
    Column("id_tipo_tarjeta", Integer, primary_key=True),
    Column("nombre", String(50), nullable=False),
    Column("categoria", String(20), nullable=False)
)
