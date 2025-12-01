from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from src.schemas.combo_detallecombo_schema import ComboSchema
from src.schemas.combo_detallecombo_schema import ComboDetalleSchema
from src.services.repositories.combo_detallecomno_service import ComboService
from src.services.repositories.combo_detallecomno_service import ComboDetalleService
from src.core.db_credentials import get_db

combos = APIRouter(tags=["Combo combo detalle"])


@combos.get("/")
def root():
    return {"message": "Ruta de combo y combo_detalle"}


@combos.post("/combos/create_combo", summary="Crear un nuevo combo")
def create_combo(data: ComboSchema, db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.create_combo(data)


@combos.post("/combos/{id_combo}/upload-image", summary="Subir imagen para un combo")
async def upload_combo_image(
        id_combo: str,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Subir una imagen para un combo específico.

    - **id_combo**: ID del combo
    - **file**: Archivo de imagen (jpg, jpeg, png, gif, webp)
    - Tamaño máximo: 5MB
    """
    service = ComboService(db)
    return await service.upload_combo_image(id_combo, file)


@combos.delete("/combos/{id_combo}/delete-image", summary="Eliminar imagen de un combo")
def delete_combo_image(id_combo: str, db: Session = Depends(get_db)):
    """
    Eliminar la imagen de un combo
    """
    service = ComboService(db)
    return service.delete_combo_image(id_combo)


@combos.get("/combos/get_all_combos/", summary="Obtener todos los combos con su detalle de platillos")
def get_all_combos(db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.get_combos_y_detalles()


@combos.get("/combos/get_combo", summary="Obtener un combo por su nombre")
def get_combo(id_combo: str, db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.get_combo_y_detalle(id_combo)


@combos.put("/combos/update_combo/{id_combo}", summary="Actualizar los datos de un combo")
def update_combo(id_combo: str, data: dict, db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.update_combo(id_combo, data)


@combos.get("/combos/get_combo_cabeza", summary="Obtener la informacion sola de los combos")
def get_all_combo_cabeza(db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.get_combo_cabeza()


@combos.get("/combos/get_combo_by_price", summary="Obtener por precio")
def get_combo_by_price(min_price: int, max_price: int, db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.get_combo_cabeza_by_price(min_price, max_price)


@combos.get("/combos/id_platos", summary="id de los platos del combo")
def get_id_platos_combo(id_combo: str, db: Session = Depends(get_db)):
    service = ComboService(db)
    return service.get_id_platillo_combo(id_combo)


# Rutas combo detalle

@combos.post("/combos/create_detalle_combo/{id_combo}", summary="Agregar platillos a un combo")
def create_combo_detalle(
        id_combo: str,
        detalles_data: List[ComboDetalleSchema],
        db: Session = Depends(get_db)
):
    print(detalles_data)
    service = ComboDetalleService(db)
    return service.create_new_combodetalle(id_combo, detalles_data)


@combos.put("/combos/update_detalle_combo/{id_detalle_combo}", summary="Actualizar el detalle de un combo")
def update_combo_detalle(id_detalle_combo: str, data: dict, db: Session = Depends(get_db)):
    service = ComboDetalleService(db)
    return service.update_combo_detalle(id_detalle_combo, data)


@combos.post("/combos/add_platillo_combo/{id_combo}", summary="Agregar platillos a un combo existente")
def add_platillo_al_combo(id_combo: str, platillos: List[ComboDetalleSchema], db: Session = Depends(get_db)):
    service = ComboDetalleService(db)
    return service.add_varios_platillos_a_combo(id_combo, platillos)


@combos.delete("/combos/delete_detalle_combo/{id_detalle_combo}", summary="Eliminar un platillo del combo")
def delete_combo_detalle(id_detalle_combo: str, db: Session = Depends(get_db)):
    service = ComboDetalleService(db)
    return service.delete_combo_detalle(id_detalle_combo)


@combos.delete("/combos/delete_all_detalle_combo/{id_combo}", summary="Eliminar todos los platillos de un combo")
def delete_all_detalle(id_combo: str, db: Session = Depends(get_db)):
    service = ComboDetalleService(db)
    return service.delete_todos_platillos_combo_detalle(id_combo)