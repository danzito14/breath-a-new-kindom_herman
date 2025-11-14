import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, delete, func, not_, true

from src.db.model.mesa_model import mesa
from src.db.model.pedidos.pedidos_model import pedido
from src.schemas.mesa_schema import MesaSchema
from src.core.db_credentials import get_db

class MesaService:
    def __init__(self, db:Session = Depends(get_db)):
        self.db = db

    def create_mesa(self, data:MesaSchema):
        mesa_dict = data.dict(exclude_unset=True)

        mesa_count = self.db.execute(
            select(func.count()).select_from(mesa).filter_by(estatus_bool=True)
        ).scalar()

        mesa_dict["Nombre_mesa"] = f"Mesa {mesa_count + 1}"
        mesa_dict["id_mesa"] = str(uuid.uuid4())
        stmt = insert(mesa).values(**mesa_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Mesa agregada exitosamente"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_mesas(self):
        try:
            stmt = (
                self.db.query(
                    mesa.c.id_mesa,
                    mesa.c.Nombre_mesa,
                    mesa.c.Capacidad,
                    pedido.c.id_pedido.label("id_pedido"),
                    mesa.c.Estado.label("Estado"),
                    mesa.c.estatus_bool
                )
                .outerjoin(
                    pedido,
                    (pedido.c.id_mesa == mesa.c.id_mesa)
                    & (not_(pedido.c.Estado.in_(["Pagada", "Cancelado"])))
                    & (mesa.c.estatus_bool == 1)
                )
                .order_by(mesa.c.Nombre_mesa)
                .all())
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))



    def get_all_mesas_ocupadas(self):
        try:
            stmt = (
                self.db.query(
                    mesa.c.id_mesa,
                    mesa.c.Nombre_mesa,
                    mesa.c.Capacidad,
                    pedido.c.id_pedido.label("id_pedido"),
                    mesa.c.Estado.label("Estado"),
                    mesa.c.estatus_bool
                )
                .outerjoin(
                    pedido,
                    (pedido.c.id_mesa == mesa.c.id_mesa)
                    & (not_(pedido.c.Estado.in_(["Pagada", "Cancelado"])))
                )
                .filter(
                    mesa.c.Estado == 'Ocupada',
                    mesa.c.estatus_bool == 1
                )
                .order_by(mesa.c.Nombre_mesa)
                .all()
            )
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))



    def get_mesa(self, Nombre_mesa:str):
        try:
            stmt = select(mesa).where(mesa.c.Nombre_mesa.ilike(f"%{Nombre_mesa}%"))
            mesas_ = self.db.execute(stmt)

            if not mesas_:
                raise HTTPException(status_code=400, detail="Mesa no encontrada")

            return [dict(row._mapping) for row in mesas_]

        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def update_mesa (self, id_mesa:str, data:dict):
        try:
            if "Nombre_mesa" in data:
                existe = self.db.execute(
                    select(mesa).where(
                        mesa.c.Nombre_mesa == data["Nombre_mesa"],
                        mesa.c.id_mesa != id_mesa
                    )
                ).first()

                if existe:
                    raise  HTTPException(
                        status_code=400,
                        detal=f"{data['Nombre_mesa']} ya esta registrada"
                    )
            stmt = (
                update(mesa).where(mesa.c.id_mesa == id_mesa).values(**data)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar los datos de Mesa"
                )

            return {"message": "Datos actualizados correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete_mesa (self, id_mesa:str):
        try:
            stmt = delete(mesa).where(mesa.c.id_mesa == id_mesa)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=400, detail="No se encontró el favorito a eliminar")

            return {"message": "Favorito eliminado correctamente"}  # ✅ respuesta útil
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))




