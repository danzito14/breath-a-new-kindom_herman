import uuid

from fastapi import Depends, HTTPException
from spyne import Integer
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, and_, true

from src.db.model.pedidos.pedidos_model import detalle_pedido, pedido
from src.db.model.platillo_model import platillo
from src.core.db_credentials import get_db

from src.db.model.pedidos.repartidores_model import repartidores
from src.schemas.pedidos.repartidor_schema import RepartidorSchema

class RepartidoresService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_repartidor(self, *args, **kwargs):
        datos_requeridos = {"id_usuario", "nombre"}

        # Soporte: recibir schema o kwargs
        if args and isinstance(args[0], RepartidorSchema):
            data_obj = args[0]
            repartidor_dict = data_obj.dict(exclude_unset=True)
            repartidor_dict["id_repartidor"] = str(uuid.uuid4())

        elif kwargs:
            print("KWARGS RECIBIDOS:", kwargs)

            missing = datos_requeridos - set(kwargs.keys())
            if missing:
                raise HTTPException(status_code=400, detail=f"Faltan los siguientes datos: {', '.join(missing)}")

            extra = set(kwargs.keys()) - datos_requeridos
            if extra:
                raise HTTPException(status_code=400, detail=f"Datos desconocidos: {', '.join(extra)}")

            id_usuario_val = kwargs["id_usuario"]
            if isinstance(id_usuario_val, tuple):
                id_usuario_val = id_usuario_val[0]

            repartidor_dict = {
                "id_repartidor": str(uuid.uuid4()),
                "id_usuario": id_usuario_val,
                "activo": False,
                "en_ruta": False,
                "pedidos_asignados": 0,
                "estado": "En local",
                "id_pedido": None
            }

        else:
            raise HTTPException(status_code=400, detail="No se recibió ningún dato")

        # 1) Validar si ya existe repartidor para ese usuario
        existe_repartidor = self.db.execute(
            select(repartidores).where(repartidores.c.id_usuario == repartidor_dict["id_usuario"])
        ).first()

        if existe_repartidor:
            raise HTTPException(status_code=409, detail="Empleado ya registrado como repartidor")

        # 2) Insertar repartidor
        try:
            stmt = insert(repartidores).values(**repartidor_dict)
            self.db.execute(stmt)
            self.db.commit()

            return {
                "message": "Repartidor creado correctamente",
                "id_usuario": repartidor_dict["id_usuario"],
                "id_repartidor": repartidor_dict["id_repartidor"]
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error al crear repartidor: {str(e)}")

    def get_all_repartidores(self):
        try:
            query = self.db.query(repartidores).all()
            return [dict(row._mapping) for row in query]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_repartidores(self, id_usuario: str, data: dict):
        try:
            # Verificar que no haya otro cocinero con el mismo id_usuario
            if "id_usuario" in data:
                existe = self.db.execute(
                    select(repartidores)
                    .where(
                        repartidores.c.id_usuario == data["id_usuario"],
                        repartidores.c.id_usuario != id_usuario
                    )
                ).first()

                if existe:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{data['id_usuario']} ya es cocinero"
                    )

            stmt = (
                update(repartidores)
                .where(repartidores.c.id_usuario == id_usuario)
                .values(**data)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar los datos de Cocinero"
                )

            return {"message": "Datos actualizados correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


