import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, delete, select, text

from src.schemas.favoritos_schema import FavoritosSchema
from src.db.model.favoritos_model import favoritos
from src.core.db_credentials import get_db

class FavoritosService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_favorito(self, data_favorito: FavoritosSchema):
        favorito_dict = data_favorito.dict(exclude_unset=True)
        favorito_dict["id_favorito"] = str(uuid.uuid4())  # ✅ generar antes del insert

        existe = self.db.execute(
            select(favoritos).where(favoritos.c.id_platillo == favorito_dict["id_platillo"])
        ).first()

        if existe:
            raise  HTTPException(status_code=400, detail="Platillo agregado ya a favoritos")

        stmt = insert(favoritos).values(**favorito_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Platillo agregado a favoritos"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_favoritos(self, id_usuario: str):
        try:
            stmt = text("""
                SELECT id_favorito, id_usuario, id_platillo, Platillo, Ruta_imagen
                FROM vista_favoritos_usuario
                   WHERE id_usuario = :id_usuario
            """)
            result = self.db.execute(stmt, {"id_usuario": id_usuario})
            return [dict(row._mapping) for row in result]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def delete_favorito(self, id_favorito: str):
        try:
            stmt = delete(favoritos).where(favoritos.c.id_favorito == id_favorito)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró el favorito a eliminar")

            return {"message": "Favorito eliminado correctamente"}  # ✅ respuesta útil
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
