import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert,select, update, delete, text
from typing import List

from src.schemas.ofertas_schema import OfertasSchema, Oferta_PlatilloSchema
from src.db.model.ofertas_model import ofertas, oferta_platillos
from src.core.db_credentials import get_db

class OfertasService:
    def __init__(self, db:Session = Depends(get_db)):
        self.db = db

    def create_oferta(self, data: OfertasSchema):
        oferta_dict = data.dict(exclude_unset=True)
        oferta_dict["id_oferta"] = str(uuid.uuid4())

        existe = self.db.execute(
            select(ofertas).where(ofertas.c.descripcion == oferta_dict["descripcion"])
        ).first()

        if existe:
            raise  HTTPException(status_code=400, detail="Error oferta ya existente")

        stmt = insert(ofertas).values(**oferta_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": "Oferta agregado a favoritos"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_ofertas(self):
        try:
            stmt = self.db.query(ofertas).all()
            return  [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def get_oferta(self, nombre_oferta:str):
        try:
            stmt = select(ofertas).where(ofertas.c.nombre_oferta.ilike(f"%{nombre_oferta}%"))
            oferta_ = self.db.execute(stmt).all()

            if not oferta_:
                raise HTTPException(status_code=400, detail="Oferta no encontrada")
                return dict(automovil_._mapping)

            return [dict(row._mapping) for row in oferta_]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def update_oferta(self, id_oferta: str, data: dict):
        try:
            if "activo" in data:
                if data["activo"] == False:
                    self.desactivar_platillos_oferta(id_oferta)
            elif "descripcion" in data:
                existe = self.db.execute(
                    select(ofertas).where(ofertas.c.descripcion == data["descripcion"])
                                          .where(ofertas.c.id_oferta != id_oferta)
                ).first()

                if existe:
                    raise HTTPException(status_code=400, detail=f"{data['apodo']} ya existe")

            stmt = (update(ofertas).where(ofertas.c.id_oferta == id_oferta).values(**data))

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se pudo actualizar los datos de la oferta")

            return {"message": "Datos actualizados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def desactivar_platillos_oferta(self, id_oferta: str):
        try:
            stmt = (
                update(oferta_platillos)
                .where(oferta_platillos.c.id_oferta == id_oferta)
                .values(activo=False)
            )
            self.db.execute(stmt)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

class Oferta_PlatilloService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_oferta_platillo(self, data: Oferta_PlatilloSchema):
        """
        Crea una o varias relaciones oferta-platillo.
        - Si `id_platillo` es una lista, se insertan todas.
        - Si es un string, se inserta solo una.
        """
        oferta_platillo_dict = data.dict(exclude_unset=True)
        id_oferta = oferta_platillo_dict["id_oferta"]
        activo = oferta_platillo_dict.get("activo", True)

        # ✅ Permitir lista o string
        id_platillos = (
            oferta_platillo_dict["id_platillo"]
            if isinstance(oferta_platillo_dict["id_platillo"], list)
            else [oferta_platillo_dict["id_platillo"]]
        )

        registros = []
        for id_platillo in id_platillos:
            # Verificar si ya existe la relación
            existe = self.db.execute(
                select(oferta_platillos)
                .where(oferta_platillos.c.id_platillo == id_platillo)
                .where(oferta_platillos.c.id_oferta == id_oferta)
            ).first()

            if existe:
                continue  # saltamos si ya existe

            registros.append({
                "id_oferta_platillo": str(uuid.uuid4()),
                "id_oferta": id_oferta,
                "id_platillo": id_platillo,
                "activo": activo
            })

        if not registros:
            raise HTTPException(status_code=400, detail="Todos los platillos ya están asignados a esta oferta")

        # ✅ Inserción en masa
        stmt = insert(oferta_platillos)
        try:
            self.db.execute(stmt, registros)
            self.db.commit()
            return {
                "message": f"Se asignaron {len(registros)} platillo(s) a la oferta correctamente",
                "registros": registros
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_ofertas_platillos(self):
        """Obtiene todas las relaciones entre ofertas y platillos"""
        try:
            stmt = self.db.query(oferta_platillos).all()
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_platillos_on_oferta_home(self):
        """Obtiene todas las relaciones entre ofertas y platillos"""
        try:
            query = text("""
             SELECT *
                FROM vista_oferta_platillo
            """)

            stmt = self.db.execute(query)
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    from sqlalchemy import text

    def get_platillos_oferta(self, id_oferta: str):
        """
        Obtiene todos los platillos asociados a una oferta específica,
        incluyendo la información completa de cada platillo.
        Puede consultar directamente una vista o hacer un JOIN manual.
        """
        try:
            # ✅ Si tienes una vista llamada 'vista_oferta_platillos'
            # (que ya junta oferta_platillo + platillo)
            query = text("""
                SELECT *
                FROM vista_oferta_platillo
                WHERE id_oferta = :id_oferta
            """)



            result = self.db.execute(query, {"id_oferta": id_oferta}).mappings().all()

            if not result:
                raise HTTPException(status_code=404, detail="No hay platillos asignados a esta oferta")

            return list(result)

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def add_varios_platillos_a_oferta(self, id_oferta: str, nuevos_platillos: List[Oferta_PlatilloSchema]):
        try:
            detalles = []
            for p in nuevos_platillos:
                detalle_dict = p.dict(exclude_unset=True)
                detalle_dict["id_oferta"] = id_oferta
                detalle_dict["id_oferta_platillo"] = str(uuid.uuid4())
                detalles.append(detalle_dict)

            stmt = insert(oferta_platillos).values(detalles)

            existe = self.db.execute(
                select(oferta_platillos).where(
                    oferta_platillos.c.id_oferta == id_oferta,
                    oferta_platillos.c.id_platillo == detalle_dict["id_platillo"]
                )
            ).first()

            if existe:
                raise HTTPException(status_code=400, detail="Este platillo ya está en la oferta")
            self.db.execute(stmt)
            self.db.commit()

            return {"message": f"{len(detalles)} platillos agregados correctamente a la oferta"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))



    def delete_oferta_platillo(self, id_oferta_platillo: str):
        try:
            stmt = delete(oferta_platillos).where(oferta_platillos.c.id_oferta_platillo == id_oferta_platillo)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontró el platillo a eliminar"
                )

            return {"message": "Detalle del platillo eliminado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete_todos_platillos_oferta_platillo(self, id_oferta: str):
        try:
            stmt = delete(oferta_platillos).where(oferta_platillos.c.id_oferta == id_oferta)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontraron platillos de esa oferta para eliminar"
                )

            return {"message": "Todos los platillos de la oferta fueron eliminados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

