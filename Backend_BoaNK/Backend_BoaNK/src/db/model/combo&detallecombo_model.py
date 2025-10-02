from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import  Table, Column, String, Boolean, CHAR, Integer
from src.core.db_credentials import meta_data

combo = Table("combo", meta_data,
                    Column("id_combo", CHAR(36), primary_key=True),
                    Column("Nombre_combo", String(100), nullable=False),
                    Column("Descripcion",String(300), nullable=False),
                    Column("Ruta_imagen", String(200), nullable=True),
                    Column("precio_combo", DECIMAL(10,2), nullable=False),
                    Column("estatus", Boolean, nullable=False)
              )


combo_detalle  = Table("combo_detalle", meta_data,
                        Column("id_detalle_combo", CHAR(36), primary_key=True),
                    Column("id_combo",String(36), nullable=False),
                    Column("id_platillo",String(36), nullable=False),
                    Column("Cantidad",Integer, nullable=False)
                       )