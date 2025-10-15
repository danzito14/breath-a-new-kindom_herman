from sqlalchemy import Table, Column, Integer, Boolean, String, Enum, DATETIME
from sqlalchemy.dialects.mysql import CHAR

from src.core.db_credentials import meta_data

cocina = Table ("cocina", meta_data,
                   Column("id_cocina", CHAR(36),primary_key=True),
                    Column("id_usuario", CHAR(36), nullable=False),
                    Column("id_detalle",	CHAR(36), nullable=True),
                    Column("estado",	Enum('Pendiente','En preparación','Listo', name="estado_enum"), nullable=False),
                    Column("hora_asignacion",	DATETIME, nullable=True),
                    Column("hora_finalizacion", DATETIME, nullable=True),
                    Column("estatus", Boolean, nullable=False),
                    Column("carga_tiempo", Integer, nullable=True)
                   )