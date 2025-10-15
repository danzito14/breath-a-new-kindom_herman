from sqlalchemy import  Table, Column, Integer,String, Enum, Boolean, CHAR
from src.core.db_credentials import meta_data

mesa = Table("mesa", meta_data,
                Column("id_mesa",CHAR(36), primary_key=True),
                Column ("Nombre_mesa", String(10), nullable=True),
                Column("Capacidad",Integer, nullable=False),
                Column("Estado",	Enum('Libre','Ocupada','Reservada', name="estado_num"), nullable=False),
                Column("estatus_bool",Boolean, nullable=False)
             )
