from sqlalchemy import Table, Column, String, DATETIME, Integer, CHAR
from src.core.db_credentials import meta_data

activar_cuenta = Table("activar_cuenta", meta_data,
                      Column("id", Integer, primary_key=True),
                       Column("correo_electronico", String, nullable=False),
                       Column("codigo", CHAR(36), nullable=False),
                       Column("create_at", DATETIME, nullable=False),
                       Column("expira_at", DATETIME, nullable=False)
                       )