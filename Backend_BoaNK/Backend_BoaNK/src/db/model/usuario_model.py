from sqlalchemy import Table, Column, Integer, String, Boolean
from sqlalchemy.dialects.mysql import CHAR
from toolz import unique

from src.core.db_credentials import engine, meta_data

usuarios = Table("usuarios", meta_data,
                 Column("id_usuario", CHAR(36), primary_key=True),
                 Column("id_nvl_usuario", Integer, nullable=False),
                 Column("Nickname",String(50), nullable=False, unique=True),
                 Column("Contraseña", String(200),nullable=False),
                 Column("Nombre",String(50), nullable=False),
                 Column("Apellido", String(50), nullable=False),
                 Column("Correo_electronico", String(100), nullable=False, unique=True),
                 Column("Num_telefonico", String(15), nullable=False),
                 Column("Ruta_imagen", String(200), nullable=True),
                 Column("estatus", Boolean, nullable=False)
                 )
meta_data.create_all(engine)

