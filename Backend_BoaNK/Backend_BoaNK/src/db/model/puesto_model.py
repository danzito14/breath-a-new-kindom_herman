from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import Table, Column, String, Boolean, Integer
from src.core.db_credentials import meta_data

puesto = Table("puesto", meta_data,
                    Column("id_puesto", Integer, primary_key=True),
                    Column("Nombre_puesto", String(50), nullable=False),
                    Column("Sueldo", DECIMAL(10,2), nullable=False),
                    Column("estatus", Boolean, nullable=True),
                    Column("id_nvl_usuario", Integer, nullable=False)
               )
