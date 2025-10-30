import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, delete, text
from src.schemas.carrito_schema import CarritoSchema, DetalleCarrito
from src.db.model.carrito_model import carrito, detalle_carrito
from src.core.db_credentials import get_db

class CarritoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # 🔹 Devuelve el id_carrito existente o lo crea si no existe
    def get_or_create_carrito(self, id_usuario: str):
        try:
            # Buscar carrito existente
            result = self.db.execute(
                select(carrito.c.id_carrito).where(carrito.c.id_usuario == id_usuario)
            ).first()

            # Si existe, devolver el id
            if result:
                return result[0]

            # Si no existe, crearlo
            id_carrito = str(uuid.uuid4())
            stmt = insert(carrito).values(id_carrito=id_carrito, id_usuario=id_usuario)
            self.db.execute(stmt)
            self.db.commit()

            return id_carrito

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error creando carrito: {str(e)}")

    def get_carrito_by_user(self, id_usuario: str):
        try:
            query = self.db.execute(text("""
                SELECT * 
                FROM db_breath_of_a_new_kingdom.vista_carrito_detalle 
                WHERE id_usuario = :id_usuario
            """), {"id_usuario": id_usuario})
            return [dict(row._mapping) for row in query]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 🔹 Agrega platillo al carrito (crea carrito si no existe)
    def agregar_platillo_carrito(self,id_usuario:str, data_carrito: DetalleCarrito):
        try:
            # Si no trae id_carrito, obtenerlo o crearlo
            if not data_carrito.id_carrito:
                id_carrito = self.get_or_create_carrito(id_usuario)
                data_carrito.id_carrito = id_carrito

            carrito_dict = data_carrito.dict(exclude_unset=True)
            carrito_dict["id_detalle_carrito"] = str(uuid.uuid4())
            stmt = insert(detalle_carrito).values(**carrito_dict)
            self.db.execute(stmt)
            self.db.commit()

            return {
                "message": "Platillo agregado correctamente",
                "id_carrito": data_carrito.id_carrito
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def eliminar_platillo(self, id_detalle_carrito: str):
        try:
            stmt = delete(detalle_carrito).where(detalle_carrito.c.id_detalle_carrito == id_detalle_carrito)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se encontró el platillo a eliminar")

            return {"message": "Platillo eliminado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
