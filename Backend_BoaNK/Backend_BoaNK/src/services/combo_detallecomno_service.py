import uuid


from fastapi import  Depends, HTTPException
from sqlalchemy.orm import  Session
from sqlalchemy import insert, select, update, delete, text
from typing import List
from collections import defaultdict

from src.db.model.combo_detallecombo_model import combo
from src.db.model.combo_detallecombo_model import combo_detalle
from src.schemas.combo_detallecombo_schema import ComboSchema
from src.schemas.combo_detallecombo_schema import ComboDetalleSchema
from src.core.db_credentials import get_db

class ComboService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_combo(self, data_combo: ComboSchema):
        combo_dict = data_combo.dict(exclude_unset =True)


        combo_dict["id_combo"] = str(uuid.uuid4())
        stmt = insert(combo).values(**combo_dict)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return {"message": "Combo registrado correctamente",
                    "id_combo": combo_dict["id_combo"] }
        except Exception as e:
            self.db.rollback()
            raise  HTTPException(status_code=400, detail=str(e))


    def get_combos_y_detalles(self):
        stmt = text("SELECT * FROM vista_combo_con_detalle")
        rows = self.db.execute(stmt).fetchall()

        combos = defaultdict(lambda: {"Nombre_combo": "", "precio_combo": 0, "platillos": []})

        for row in rows:
            combo_id = row.id_combo
            combos[combo_id]["Nombre_combo"] = row.Nombre_combo
            combos[combo_id]["precio_combo"] = row.precio_combo
            combos[combo_id]["platillos"].append({
                "id_detalle_combo": row.id_detalle_combo,
                "id_platillo": row.id_platillo,
                "Nombre_platillo": row.Nombre_platillo,
                "precio_platillo": row.precio_platillo,
                "Cantidad": row.cantidad
            })

        return [{"id_combo": k, **v} for k, v in combos.items()]



    def get_combo_y_detalle(self, Nombre_combo: str):
        try:
            # ✅ Usamos parámetros para evitar inyección SQL y corregimos '='
            stmt = text("""
                SELECT * 
                FROM vista_combo_con_detalle 
                WHERE Nombre_combo = :nombre
            """)

            rows = self.db.execute(stmt, {"nombre": Nombre_combo}).fetchall()

            if not rows:
                raise HTTPException(status_code=404, detail="Combo no encontrado")

            combo_info = {
                "id_combo": rows[0].id_combo,
                "Nombre_combo": rows[0].Nombre_combo,
                "precio_combo": rows[0].precio_combo,
                "platillos": []
            }

            for row in rows:
                combo_info["platillos"].append({
                    "id_detalle_combo": row.id_detalle_combo,
                    "id_platillo": row.id_platillo,
                    "Nombre_platillo": row.Nombre_platillo,
                    "precio_platillo": row.precio_platillo,
                    "Cantidad": row.cantidad
                })

            return combo_info


        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def update_combo(self, id_combo: str, data: dict):

        try:
            stmt = update(combo).where(combo.c.id_combo == id_combo).values(**data)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar el combo (ID no encontrado)"
                )

            return {"message": "Datos actualizados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))


class ComboDetalleService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_new_combodetalle(self, id_combo: str, data_detalles: List[ComboDetalleSchema]):
        detalles_list = []
        for detalle in data_detalles:
            detalle_dict = detalle.dict()
            detalle_dict["id_combo"] = id_combo
            detalle_dict["id_detalle_combo"] = str(uuid.uuid4())  # ✅ Agregar esta línea
            detalles_list.append(detalle_dict)

        nombre_combo = self.conseguir_nombre_combo(id_combo)
        stmt = insert(combo_detalle).values(detalles_list)

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": f"{len(detalles_list)} platillos del combo '{nombre_combo}' registrados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def update_combo_detalle(self, id_detalle_combo: str, data: dict):
        try:
            stmt = (
                update(combo_detalle)
                .where(combo_detalle.c.id_detalle_combo == id_detalle_combo)
                .values(**data)
            )
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se pudo actualizar el detalle del combo (ID no encontrado)"
                )

            return {"message": "Detalle del combo actualizado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def add_varios_platillos_a_combo(self, id_combo: str, nuevos_platillos: List[ComboDetalleSchema]):
        try:
            detalles = []
            for p in nuevos_platillos:
                detalle_dict = p.dict(exclude_unset=True)
                detalle_dict["id_combo"] = id_combo
                detalle_dict["id_detalle_combo"] = str(uuid.uuid4())
                detalles.append(detalle_dict)

            stmt = insert(combo_detalle).values(detalles)

            existe = self.db.execute(
                select(combo_detalle).where(
                    combo_detalle.c.id_combo == id_combo,
                    combo_detalle.c.id_platillo == detalle_dict["id_platillo"]
                )
            ).first()

            if existe:
                raise HTTPException(status_code=400, detail="Este platillo ya está en el combo")
            self.db.execute(stmt)
            self.db.commit()

            return {"message": f"{len(detalles)} platillos agregados correctamente al combo"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete_combo_detalle(self, id_detalle_combo: str):
        try:
            stmt = delete(combo_detalle).where(combo_detalle.c.id_detalle_combo == id_detalle_combo)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontró el detalle del combo a eliminar"
                )

            return {"message": "Detalle del combo eliminado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def delete_todos_platillos_combo_detalle(self, id_combo: str):
        try:
            stmt = delete(combo_detalle).where(combo_detalle.c.id_combo == id_combo)
            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontraron platillos de ese combo para eliminar"
                )

            return {"message": "Todos los platillos del combo fueron eliminados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))



    def conseguir_nombre_combo(self, id_combo):
        try:
            nombre_combo = self.db.execute(
                select(combo.c.Nombre_combo).where(combo.c.id_combo == id_combo)
            ).first()

            return nombre_combo[0] if nombre_combo else None
        except Exception as e:
            self.db.rollback()
            raise  HTTPException(status_code=400, detail=str(e))