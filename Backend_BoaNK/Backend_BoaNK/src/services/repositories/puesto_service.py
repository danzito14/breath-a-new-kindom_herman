from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update

from src.db.model.empleado_model import empleado
from src.db.model.usuario_model import usuarios
from src.schemas.puesto_schema import PuestoSchema
from src.db.model.puesto_model import puesto
from src.core.db_credentials import get_db

class PuestoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_puesto(self, data_puesto: PuestoSchema):
        puesto_dict = data_puesto.dict(exclude_unset=True)

        stmt = insert(puesto).values(**puesto_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Puesto registrado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_puestos(self):
        try:
            query = self.db.query(puesto).all()  # ✅ corregido: antes consultaba empleado
            return [dict(row._mapping) for row in query]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_puesto(self, id_puesto: int):
        spuesto = (
            self.db.query(puesto)
            .filter(puesto.c.id_puesto == id_puesto)
            .first()
        )
        if not spuesto:
            raise HTTPException(status_code=404, detail="Puesto no encontrado")
        return dict(spuesto._mapping)  # ✅ ahora sí retorna el resultado

    def update_puesto(self, id_puesto: int, data: dict):
        # 1. Obtener estado actual del puesto
        query_estado = select(puesto.c.estatus).where(puesto.c.id_puesto == id_puesto)
        estado_actual = self.db.execute(query_estado).scalar()

        if estado_actual is None:
            raise HTTPException(
                status_code=404,
                detail="El puesto no existe"
            )

        nuevo_estado = data.get("estatus")

        # 2. Buscar empleados que tienen este puesto
        query_empleados = select(empleado.c.id_usuario).where(empleado.c.id_puesto == id_puesto)
        empleados_ids = [row[0] for row in self.db.execute(query_empleados).all()]

        # 3. Si el puesto pasa de activo → inactivo → desactivar usuarios
        if estado_actual == 1 and nuevo_estado == 0:
            if empleados_ids:
                stmt_desactivar = (
                    update(usuarios)
                    .where(usuarios.c.id_usuario.in_(empleados_ids))
                    .values(estatus=0)
                )
                self.db.execute(stmt_desactivar)
                print("Usuarios desactivados:", empleados_ids)

        # 4. Si el puesto pasa de inactivo → activo → reactivar usuarios
        if estado_actual == 0 and nuevo_estado == 1:
            if empleados_ids:
                stmt_activar = (
                    update(usuarios)
                    .where(usuarios.c.id_usuario.in_(empleados_ids))
                    .values(estatus=1)
                )
                self.db.execute(stmt_activar)
                print("Usuarios reactivados:", empleados_ids)

        # 5. Actualizar el puesto normalmente
        stmt = (
            update(puesto)
            .where(puesto.c.id_puesto == id_puesto)
            .values(**data)
        )
        result = self.db.execute(stmt)
        self.db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="No se pudo actualizar los datos del puesto (ID no encontrado)"
            )

        return {"message": "Datos actualizados correctamente"}
