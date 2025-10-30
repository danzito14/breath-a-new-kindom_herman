from sqlalchemy import Table, Column, String, Boolean, DECIMAL, DATETIME
from sqlalchemy.dialects.mysql import  CHAR, DECIMAL

from src.core.db_credentials import meta_data

ofertas = Table ("ofertas", meta_data,
                    Column("id_oferta",	CHAR(36), primary_key=True),
                    Column("nombre_oferta",String(100), nullable = False),
                    Column("descripcion", String, nullable=False),
                    Column("porcentaje_descuento", DECIMAL(5,2), nullable=False),
                    Column("fecha_inicio", DATETIME, nullable=False),
                    Column("fecha_fin",DATETIME, nullable=False),
                    Column("activo",	Boolean, nullable=False)
                 )

oferta_platillos = Table ("oferta_platillos", meta_data,
                     Column("id_oferta_platillo", CHAR(36), primary_key=True),
                    Column("id_platillo",CHAR(36), nullable=False),
                    Column("id_oferta",CHAR(36), nullable=False),
                    Column("activo",Boolean, nullable=False)
                         )