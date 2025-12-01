import uuid
import os
from pathlib import Path
from fastapi import Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import insert, select, update, delete, text
from typing import List, Optional
from collections import defaultdict

from src.db.model.combo_detallecombo_model import combo
from src.db.model.combo_detallecombo_model import combo_detalle
from src.schemas.combo_detallecombo_schema import ComboSchema
from src.schemas.combo_detallecombo_schema import ComboDetalleSchema
from src.core.db_credentials import get_db

# Configuración de rutas para imágenes
UPLOAD_DIR = Path("public/combos")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Crear directorio si no existe
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ComboService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_combo(self, data_combo: ComboSchema):
        combo_dict = data_combo.dict(exclude_unset=True)
        combo_dict["id_combo"] = str(uuid.uuid4())

        stmt = insert(combo).values(**combo_dict)
        try:
            result = self.db.execute(stmt)
            self.db.commit()
            return {
                "message": "Combo registrado correctamente",
                "id_combo": combo_dict["id_combo"]
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    async def upload_combo_image(self, id_combo: str, file: UploadFile) -> dict:
        """
        Subir imagen para un combo
        """
        try:
            # Validar que el combo existe
            combo_exists = self.db.execute(
                select(combo).where(combo.c.id_combo == id_combo)
            ).first()

            if not combo_exists:
                raise HTTPException(status_code=404, detail="Combo no encontrado")

            # Validar extensión del archivo
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Extensión no permitida. Use: {', '.join(ALLOWED_EXTENSIONS)}"
                )

            # Leer contenido del archivo
            contents = await file.read()

            # Validar tamaño
            if len(contents) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo muy grande. Máximo {MAX_FILE_SIZE / (1024 * 1024)}MB"
                )

            # Eliminar imagen anterior si existe
            if combo_exists.Ruta_imagen:
                old_image_path = Path(combo_exists.Ruta_imagen)
                if old_image_path.exists():
                    old_image_path.unlink()

            # Generar nombre único para el archivo
            unique_filename = f"{id_combo}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename

            # Guardar archivo
            with open(file_path, "wb") as f:
                f.write(contents)

            # Actualizar ruta en la base de datos
            relative_path = f"public/combos/{unique_filename}"
            stmt = update(combo).where(
                combo.c.id_combo == id_combo
            ).values(Ruta_imagen=relative_path)

            self.db.execute(stmt)
            self.db.commit()

            return {
                "message": "Imagen subida correctamente",
                "ruta": relative_path,
                "filename": unique_filename
            }

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            # Eliminar archivo si se guardó pero falló la BD
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=400, detail=f"Error al subir imagen: {str(e)}")

    def delete_combo_image(self, id_combo: str) -> dict:
        """
        Eliminar imagen de un combo
        """
        try:
            combo_data = self.db.execute(
                select(combo).where(combo.c.id_combo == id_combo)
            ).first()

            if not combo_data:
                raise HTTPException(status_code=404, detail="Combo no encontrado")

            if not combo_data.Ruta_imagen:
                raise HTTPException(status_code=404, detail="El combo no tiene imagen")

            # Eliminar archivo físico
            image_path = Path(combo_data.Ruta_imagen)
            if image_path.exists():
                image_path.unlink()

            # Actualizar base de datos
            stmt = update(combo).where(
                combo.c.id_combo == id_combo
            ).values(Ruta_imagen=None)

            self.db.execute(stmt)
            self.db.commit()

            return {"message": "Imagen eliminada correctamente"}

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_combos_y_detalles(self):
        stmt = text("SELECT * FROM vista_combo_con_detalle")
        rows = self.db.execute(stmt).fetchall()

        combos = defaultdict(lambda: {
            "Nombre_combo": "",
            "Descripcion": "",
            "Ruta_imagen": None,
            "precio_combo": 0,
            "estatus": 0,
            "platillos": []
        })

        for row in rows:
            combo_id = row.id_combo
            combos[combo_id]["Nombre_combo"] = row.Nombre_combo
            combos[combo_id]["Descripcion"] = getattr(row, 'Descripcion', '')
            combos[combo_id]["Ruta_imagen"] = getattr(row, 'Ruta_imagen', None)
            combos[combo_id]["precio_combo"] = row.precio_combo
            combos[combo_id]["estatus"] = getattr(row, 'estatus', 1)
            combos[combo_id]["platillos"].append({
                "id_detalle_combo": row.id_detalle_combo,
                "id_platillo": row.id_platillo,
                "Nombre_platillo": row.Nombre_platillo,
                "precio_platillo": row.precio_platillo,
                "Cantidad": row.cantidad
            })

        return [{"id_combo": k, **v} for k, v in combos.items()]

    def get_combo_y_detalle(self, id_combo: str):
        try:
            stmt = text("""
                SELECT * 
                FROM vista_combo_con_detalle 
                WHERE id_combo = :id_combo
            """)

            rows = self.db.execute(stmt, {"id_combo": id_combo}).fetchall()

            if not rows:
                raise HTTPException(status_code=404, detail="Combo no encontrado")

            combo_info = {
                "id_combo": rows[0].id_combo,
                "Nombre_combo": rows[0].Nombre_combo,
                "Descripcion": getattr(rows[0], 'Descripcion', ''),
                "Ruta_imagen": getattr(rows[0], 'Ruta_imagen', None),
                "precio_combo": rows[0].precio_combo,
                "estatus": getattr(rows[0], 'estatus', 1),
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

    def get_id_platillo_combo(self, id_combo: str):
        try:
            stmt = text("""
                WITH RECURSIVE numeros AS (
                    SELECT 1 AS n
                    UNION ALL
                    SELECT n + 1 FROM numeros WHERE n < 100
                )
                SELECT v.id_platillo
                FROM vista_combo_con_detalle v
                JOIN numeros n ON n.n <= v.cantidad
                WHERE v.id_combo = :id_combo;
            """)

            rows = self.db.execute(stmt, {"id_combo": id_combo}).fetchall()

            if not rows:
                raise HTTPException(status_code=404, detail="Combo no encontrado")

            return [dict(row._mapping) for row in rows]

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_combo_cabeza(self):
        try:
            stmt = self.db.execute(
                select(combo)
            ).all()
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_combo_cabeza_by_price(self, min_price: int, max_price: int):
        try:
            stmt = self.db.execute(
                select(combo).where(
                    (combo.c.precio_combo >= min_price) & (combo.c.precio_combo <= max_price)
                )
            ).all()
            return [dict(row._mapping) for row in stmt]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


class ComboDetalleService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_new_combodetalle(self, id_combo: str, data_detalles: List[ComboDetalleSchema]):
        detalles_list = []
        for detalle in data_detalles:
            detalle_dict = detalle.dict()
            detalle_dict["id_combo"] = id_combo
            detalle_dict["id_detalle_combo"] = str(uuid.uuid4())
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

                existe = self.db.execute(
                    select(combo_detalle).where(
                        combo_detalle.c.id_combo == id_combo,
                        combo_detalle.c.id_platillo == detalle_dict["id_platillo"]
                    )
                ).first()

                if existe:
                    raise HTTPException(status_code=400, detail="Este platillo ya está en el combo")

                detalles.append(detalle_dict)

            stmt = insert(combo_detalle).values(detalles)
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
            raise HTTPException(status_code=400, detail=str(e))