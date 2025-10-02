from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Table, Column, String, Boolean, Date, Integer
from src.core.db_credentials import meta_data

empleado = Table("empleado", meta_data,
                    Column ("id_empleado", CHAR(36), primary_key=True),
                    Column ( "id_puesto", Integer, nullable=False),
                    Column ("id_uniforme", Integer, nullable=False),
                    Column ("Nombre", String(50), nullable=False),
                    Column ("Apellido", String(50), nullable=False),
                    Column("Correo_electronico", String(100), nullable=False),
                    Column ("Num_telefonico",String(15), nullable=False),
                    Column ("Calle",String(100), nullable=False),
                    Column ("No_ext", String(10), nullable=False),
                    Column ("No_int",String(10), nullable=True),
                    Column ("Colonia", String(100), nullable=False),
                    Column ("CP", String(5), nullable=False),
                    Column ("Ciudad", String(100), nullable=False),
                    Column ("Municipio", String(100), nullable=False),
                    Column ("Estado",String(30), nullable=False),
                    Column ("Fecha_de_contratacion", Date, nullable=False),
                    Column ("Fecha_de_despido", Date, nullable=True),
                    Column ("Razon_despido", String(500), nullable=True),
                    Column ("Fecha_de_recontratacion", Date, nullable=True),
                    Column ("id_usuario", CHAR(36), nullable=True),
                    Column ("estatus", Boolean, nullable=False),
                    Column("Ruta_imagen", String(200), nullable=True)
                )
