from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Table, Column,Date
from src.core.db_credentials import meta_data

favoritos = Table ("favoritos", meta_data,
                   Column("id_favorito", CHAR(36), primary_key=True),
                    Column("id_usuario", CHAR(36), nullable=False),
                    Column("id_platillo", CHAR(36), nullable=False),
                    Column("fecha_agregado", Date, nullable=False)
)
