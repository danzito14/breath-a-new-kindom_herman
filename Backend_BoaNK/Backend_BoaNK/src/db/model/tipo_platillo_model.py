from sqlalchemy import Table, Column,Integer, Boolean, String
from src.core.db_credentials import meta_data

tipo_platillo = Table ("tipo_platillo", meta_data,
                  Column("id_tipo_platillo",Integer, primary_key=True),
                  Column("descripcion",String(50), nullable=False),
                  Column("estatus",Boolean, nullable=False),
                  Column("ruta_icono", String, nullable=False),
                  Column("color", String, nullable=False)
                       )
