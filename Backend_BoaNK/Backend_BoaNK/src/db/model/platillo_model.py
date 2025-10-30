from tokenize import String

from sqlalchemy import Table, Column, Integer, String, Boolean, DECIMAL
from sqlalchemy.dialects.mysql import  CHAR

from src.core.db_credentials import engine, meta_data

platillo = Table("platillo", meta_data,
                 Column ("id_platillo", CHAR(36), primary_key=True),
                       Column ("id_tipo_platillo", Integer, nullable=False),
                       Column ("Nombre_platillo", String(100), nullable=False),
                       Column ("Ruta_imagen", String(200), nullable=False),
                       Column ("precio_produccion", DECIMAL(10,2), nullable=False),
                       Column("precio_venta", DECIMAL(10, 2), nullable=False),
                       Column("estatus", Boolean, nullable=False),
                       Column("Descripcion", String(100), nullable=False),
                       Column("tiempo_preparacion", Integer, nullable=False),

                        #Columnas para el front para poner oferta o no
                        En_oferta=Column(Boolean),
                        Porcentaje_oferta= Column(String),
                        precio_original=Column(String)
                 )

opcion_platillo = Table("opcion_platillo", meta_data,
                        Column("id_option", Integer, primary_key=True),
                        Column("id_platillo", CHAR(36), nullable=False),
                        Column("opcion", String(45), nullable=False),
                        Column("precio", DECIMAL(5, 2), nullable=False)
                        )
