from fastapi import  Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db


class home_needs:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_min_and_max_price(self):
        try:
            query = text("""
                                SELECT
                  MIN(precio) AS min_price,
                  MAX(precio) AS max_price
                FROM (
                  SELECT precio_venta AS precio FROM platillo WHERE estatus = 1
                  UNION ALL
                  SELECT precio_combo AS precio FROM combo WHERE estatus = 1
                ) AS todos_los_precios;
            """)
            result = self.db.execute(query)
            row = result.fetchone()
            return dict(row._mapping) if row else {}
        except Exception as e:
            HTTPException(status_code=400, detail=str(e))