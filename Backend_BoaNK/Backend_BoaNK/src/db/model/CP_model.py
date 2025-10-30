from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import Table, Column, String,Integer
from src.core.db_credentials import meta_data

cp = Table ("cp", meta_data,
            Column("codigo",Integer, primary_key= True),
            Column("Colonia", String, nullable=False),
            Column("Municipio",String, nullable=False),
            Column("Estado", String, nullable=False),
            Column("Ciudad", String, nullable=False)
            )