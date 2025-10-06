from sqlalchemy import Table, Column, String, Enum, Integer, Boolean
from src.core.db_credentials import meta_data

uniforme = Table("uniforme", meta_data,
                Column("id_uniforme",	Integer, primary_key=True),
                Column("id_puesto", Integer, nullable=False),
                Column("Talla", Enum('XS','S','M','L','XL','XXL', name="talla_num" ), nullable=False),
                Column("Descripcion",	String(100), nullable=False),
                Column("estatus", Boolean, nullable=False)
                 )


