from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Table, Column, String, Boolean
from src.core.db_credentials import meta_data

direcciones_usuario = Table ("direcciones_usuario", meta_data,
                    Column ("id_direccion",CHAR(36), primary_key=True),
                    Column("id_usuario",CHAR(36), nullable=False),
                    Column("alias",	String(50), nullable=False),
                    Column("Calle",String(100), nullable=False),
                    Column("No_ext",String(10), nullable=False),
                    Column("No_int",String(10), nullable=True),
                    Column("Colonia",String(100), nullable=False),
                    Column("CP",CHAR(5), nullable=False),
                    Column("Ciudad", String(100), nullable=False),
                    Column("Municipio",	String(100), nullable=False),
                    Column("Estado",String(30), nullable=False),
                    Column("predeterminada", Boolean, nullable=False),
                    Column("instrucciones_add", String(200), nullable=True)
                    )

