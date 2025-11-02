import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, update, select

from src.schemas.pedidos.pedidostemporal_schema import pedido_temporalSchema
from src.db.model.pedidos.pedido_temporal import pedido_temporal
from src.core.db_credentials import get_db


class PedidoTemporalService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_or_update_temporal(self, data_temporal: pedido_temporalSchema):
        """
        Crea o actualiza un pedido temporal según el id_usuario.
        Si ya existe uno, se actualiza con el nuevo contenido.
        """
        temporal_dict = data_temporal.dict(by_alias=False, exclude_unset=True)

        # Verificar si ya existe pedido temporal del usuario
        result = self.db.execute(
            select(pedido_temporal).where(
                pedido_temporal.c.id_usuario == temporal_dict["id_usuario"]
            )
        ).fetchone()

        try:
            if result:
                valores_update = {
                    "datos_pedido": temporal_dict["datos_pedido"],
                    "fecha_creacion": data_temporal.fecha_creacion,
                    "precio": data_temporal.precio,
                    "lista_producto": temporal_dict["lista_producto"],
                }

                # Solo agregamos los opcionales si existen
                if temporal_dict.get("id_mesa") is not None:
                    valores_update["id_mesa"] = temporal_dict["id_mesa"]

                if temporal_dict.get("id_direccion") is not None:
                    valores_update["id_direccion"] = temporal_dict["id_direccion"]

                # Creamos la sentencia UPDATE
                stmt = (
                    update(pedido_temporal)
                    .where(pedido_temporal.c.id_usuario == temporal_dict["id_usuario"])
                    .values(**valores_update)
                )

                mensaje = "Pedido temporal actualizado correctamente"
            else:
                temporal_dict["id_temporal"] = str(uuid.uuid4())
                stmt = insert(pedido_temporal).values(**temporal_dict)
                mensaje = "Pedido temporal creado correctamente"

            self.db.execute(stmt)
            self.db.commit()

            return {
                "message": mensaje,
                "id_usuario": temporal_dict["id_usuario"],
                "id_temporal": temporal_dict.get("id_temporal", result.id_temporal if result else None)
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error al crear o actualizar pedido temporal: {e}"
            )

    def delete_temporal(self, id_usuario: str):
        """
        Elimina el pedido temporal de un usuario, por ejemplo, si se arrepiente o paga.
        """
        try:
            stmt = pedido_temporal.delete().where(pedido_temporal.c.id_usuario == id_usuario)
            self.db.execute(stmt)
            self.db.commit()
            return {"message": f"Pedido temporal del usuario {id_usuario} eliminado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al eliminar pedido temporal: {e}")

    def get_temporal(self, id_usuario: str):
        """
        Recupera el pedido temporal actual de un usuario.
        """
        try:
            stmt = select(pedido_temporal).where(pedido_temporal.c.id_usuario == id_usuario)
            result = self.db.execute(stmt).fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="No existe pedido temporal para este usuario")
            return dict(result._mapping)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al obtener pedido temporal: {e}")

    def update_temporal(self, id_usuario: str, data: dict):
        try:
            print("🧾 Datos recibidos en update_temporal:")
            stmt = (
                update(pedido_temporal)
                .where(pedido_temporal.c.id_usuario == id_usuario)
                .values(**data)
            )
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró el temporal")

            return {"message": "Datos actualizados correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
