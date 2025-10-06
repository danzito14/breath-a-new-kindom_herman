from sqlalchemy.dialects.mysql import  CHAR, YEAR
from sqlalchemy import Table, Column, String, DATE, Enum
from src.core.db_credentials import meta_data

automovil = Table("automovil", meta_data,
                    Column("id_auto",	CHAR(36), primary_key=True),
                    Column("Marca",	String(50), nullable=False),
                    Column("Modelo",	String(50), nullable=False),
                    Column("Año",	YEAR, nullable=False),
                    Column("Placas",	String(10), nullable=False),
                    Column("Color",	String(30), nullable=False),
                    Column("Fecha_compra",	DATE, nullable=False),
                    Column("Estado", Enum("Activo", "En mantenimiento", "Baja", name="estado_enum"), nullable=False),
                    Column("id_empleado",	CHAR(36), nullable=False),
                    Column ("apodo", String(30), nullable=False)
                  )
