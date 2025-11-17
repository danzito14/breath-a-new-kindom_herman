import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from fastapi import Depends, HTTPException
from pyDatalog.examples.python import result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, and_, true

from src.db.model.cocineros_model import cocina
from src.db.model.pedidos.pedidos_model import detalle_pedido, pedido
from src.db.model.platillo_model import platillo
from src.schemas.cocineros_schemas import CocinaSchema
from src.core.db_credentials import get_db

class CocinerosService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_cocinero(self, *args, **kwargs):
        datos_requeridos = {"id_usuario", "nombre"}

        # soporte por compatibilidad: recibir un schema o kwargs
        if args and isinstance(args[0], CocinaSchema):
            data_obj = args[0]
            cocina_dict = data_obj.dict(exclude_unset=True)
            cocina_dict["id_cocina"] = str(uuid.uuid4())
        elif kwargs:
            print("KWARGS RECIBIDOS:", kwargs)
            missing = datos_requeridos - set(kwargs.keys())
            if missing:
                raise HTTPException(status_code=400, detail=f"Faltan los siguientes datos: {', '.join(missing)}")
            extra = set(kwargs.keys()) - datos_requeridos
            if extra:
                raise HTTPException(status_code=400, detail=f"Datos desconocidos o no esperados: {', '.join(extra)}")

            # Construyo el dict con defaults necesarios
            id_usuario_val = kwargs["id_usuario"]
            if isinstance(id_usuario_val, tuple):
                id_usuario_val = id_usuario_val[0]  # toma solo el string
            print(id_usuario_val)
            cocina_dict = {
                "id_cocina": str(uuid.uuid4()),
                "id_usuario": id_usuario_val,
                "id_detalle": None,
                "estado": "Pendiente",
                "hora_asignacion": None,
                "hora_finalizacion": None
            }
        else:
            raise HTTPException(status_code=400, detail="No se recibió ningún dato")

        # 1) ¿ya existe un cocinero para ese id_usuario?
        existe_empleado = self.db.execute(
            select(cocina).where(cocina.c.id_usuario == cocina_dict["id_usuario"])
        ).first()
        if existe_empleado:
            # Indica claramente que el empleado ya está registrado como cocinero
            raise HTTPException(status_code=409, detail="Empleado ya registrado como cocinero")

        # 2) ¿el id_usuario ya lo usa otro cocinero?
        existe_id_usuario = self.db.execute(
            select(cocina).where(cocina.c.id_cocina == cocina_dict["id_usuario"])
        ).first()
        if existe_id_usuario:
            raise HTTPException(status_code=400,
                                detail=f"El id_usuario '{cocina_dict['id_usuario']}' ya está en uso por otro cocinero")

        # Insertar
        try:
            stmt = insert(cocina).values(**cocina_dict)
            self.db.execute(stmt)
            self.db.commit()
            return {
                "message": "Cocinero creado correctamente",
                "id_usuario": cocina_dict["id_usuario"],
                "id_cocina": cocina_dict["id_cocina"]
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"{str(e)} asasasas")

    def get_all_cocina(self):
        try:
            query = self.db.query(cocina).all()
            return [dict(row._mapping) for row in query]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_cocinero(self, id_usuario: str, data: dict):
        try:
            # Verificar que no haya otro cocinero con el mismo id_usuario
            if "id_usuario" in data:
                existe = self.db.execute(
                    select(cocina)
                    .where(
                        cocina.c.id_usuario == data["id_usuario"],
                        cocina.c.id_usuario != id_usuario
                    )
                ).first()

                if existe:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{data['id_usuario']} ya es cocinero"
                    )

            stmt = (
                update(cocina)
                .where(cocina.c.id_usuario == id_usuario)
                .values(**data)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar los datos de Cocinero"
                )

            return {"message":"Datos actualizados correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


    def update_cocinero_plato(self, id_usuario: str, data: dict):
        try:
            # Verificar que no haya otro cocinero con el mismo id_usuario
            if "id_usuario" in data:
                existe = self.db.execute(
                    select(cocina)
                    .where(
                        cocina.c.id_usuario == data["id_usuario"],
                        cocina.c.id_usuario != id_usuario
                    )
                ).first()

                if existe:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{data['id_usuario']} ya es cocinero"
                    )

            stmt = (
                update(cocina)
                .where(and_(cocina.c.id_usuario == id_usuario,  cocina.c.estatus == true()))
                .values(**data)
            )

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar los datos de Cocinero"
                )

            return {"message":"Datos actualizados correctamente"}

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    from sqlalchemy import select, update
    from sqlalchemy.exc import SQLAlchemyError
    from fastapi import HTTPException

    from sqlalchemy import select, update
    from sqlalchemy.exc import SQLAlchemyError
    from fastapi import HTTPException



    def asignar_plato(self, id_usuario: str):
        """
        Asigna atómicamente el siguiente platillo pendiente al cocinero.

        Returns:
            dict: {"id_detalle": str} si hay platillo disponible
            None: si no hay platillos pendientes
        """
        try:
            with self.db.begin():
                # 1️⃣ Verificar que el cocinero no tenga ya un platillo asignado
                cocinero_actual = self.db.execute(
                    select(cocina)
                    .where(cocina.c.id_usuario == id_usuario)
                ).first()

                if not cocinero_actual:
                    raise HTTPException(
                        status_code=404,
                        detail="Cocinero no encontrado"
                    )

                cocinero_dict = dict(cocinero_actual._mapping)

                # Si ya tiene platillo asignado, devolver ese
                if cocinero_dict.get("id_detalle"):
                    print(f"⚠️ Cocinero {id_usuario} ya tiene platillo: {cocinero_dict['id_detalle']}")
                    return {
                        "id_detalle": cocinero_dict["id_detalle"]
                    }

                # 2️⃣ Buscar el primer platillo pendiente libre (con bloqueo)
                query = (
                    select(detalle_pedido)
                    .join(pedido, pedido.c.id_pedido == detalle_pedido.c.id_pedido)
                    .where(detalle_pedido.c.estado == "pendiente")
                    .order_by(pedido.c.Fecha)
                    .with_for_update(skip_locked=True)  # 🔥 Evita conflictos entre cocineros
                    .limit(1)
                )

                plato = self.db.execute(query).first()

                if not plato:
                    print("ℹ️ No hay platillos pendientes disponibles")
                    return None  # No hay platos pendientes

                plato = plato._mapping
                plato_id = plato["id_detalle"]

                print(f"✅ Asignando platillo {plato_id} a cocinero {id_usuario}")

                # 3️⃣ Actualizar el platillo a "cocinando"
                upd_plato = (
                    update(detalle_pedido)
                    .where(detalle_pedido.c.id_detalle == plato_id)
                    .values(estado="cocinando")
                )
                self.db.execute(upd_plato)

                # 4️⃣ Asignar el platillo al cocinero
                upd_cocinero = (
                    update(cocina)
                    .where(cocina.c.id_usuario == id_usuario)
                    .values(id_detalle=plato_id)
                )
                result = self.db.execute(upd_cocinero)

                if result.rowcount == 0:
                    raise HTTPException(
                        status_code=500,
                        detail="No se pudo asignar el platillo al cocinero"
                    )

            # 5️⃣ Devolver solo el ID (el frontend cargará los detalles)
            return {
                "id_detalle": plato_id
            }

        except HTTPException:
            raise  # Re-lanzar excepciones HTTP
        except SQLAlchemyError as e:
            print(f"❌ Error de base de datos: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al asignar platillo: {str(e)}"
            )
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado: {str(e)}"
            )


    def tiene_plato(self, id_usuario: str):
        """
        Verifica si el cocinero tiene un platillo asignado.

        Returns:
            list: [{"id_detalle": str, ...}] si tiene platillo asignado
            None: si no tiene platillo asignado o no existe el cocinero
        """
        try:
            result = self.db.execute(
                select(cocina).where(cocina.c.id_usuario == id_usuario)
            ).first()

            if not result:
                return None  # No existe el cocinero

            data = dict(result._mapping)

            # Si tiene platillo asignado, devolverlo en formato lista
            if data.get("id_detalle") is not None:
                return [data]
            else:
                return None  # Cocinero existe pero sin platillo asignado

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))