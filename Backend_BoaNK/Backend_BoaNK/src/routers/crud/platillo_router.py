import uuid
from datetime import datetime

from src.schemas.platillos_schema import PlatilloSchema, OpcionplatilloSchema
from src.db.model.platillo_model import platillo, opcion_platillo
from src.db.model.tipo_platillo_model import tipo_platillo
from src.db.model.ofertas_model import ofertas, oferta_platillos
from src.core.db_credentials import get_db
from fastapi import Body, APIRouter, Depends, HTTPException
from sqlalchemy.orm import  Session
from sqlalchemy import insert, select, update, delete, func, and_


platillos = APIRouter(tags=["Platillos"])

@platillos.get("/platillo")
def root():
    return {"mesage":"Welcome to Breath of a New Kingdom"}

@platillos.post("/platillo/create_platillo")
def create_platillo(data_platillo: PlatilloSchema, db: Session = Depends(get_db)):

    #Generar el id
    platillo_dict = data_platillo.dict(exclude_unset=True)
    platillo_dict ["id_platillo"] = str(uuid.uuid4())

    #Generamos el stmt
    stmt = insert(platillo).values(**platillo_dict)
    try:
        db.execute(stmt)
        db.commit()
        return {"message":"Platillo creado correctamente", "nombre": platillo_dict["Nombre_platillo"]}
    except Exception as e:
        db.roolback()
        raise  HTTPException(status_code=400, detail=str(e))



@platillos.post("/platillo/create_options_platillo", summary="Darle opciones de personalizacion a un platillo")
def create_option_platillo(data_option: OpcionplatilloSchema, db:Session  =Depends(get_db)):
    try:
        data_dict = data_option.dict(exclude_unset=True)

        stmt = select(opcion_platillo).where(
            (opcion_platillo.c.opcion == data_dict["opcion"]) &
            (opcion_platillo.c.id_platillo == data_dict["id_platillo"])
        )

        existe_option = db.execute(stmt).fetchone()

        if existe_option:
         raise HTTPException(status_code=400, detail="Opcion de plato existente")

        stmt = insert(opcion_platillo).values(**data_dict)
        try:
            db.execute(stmt)
            db.commit()
            return {"message": "Opcion de personalizacion de plato agregada correctamente", "nombre": data_dict["opcion"]}
        except Exception as e:
            db.roolback()
            raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise  HTTPException (status_code=400, detail=str(e))



@platillos.get("/platillos/get_platillo_option", summary="Obtener las opciones de un platillo")
def get_option_platillo(id_platillo:str, db:Session = Depends(get_db)):
    stmt = db.query(opcion_platillo).where(opcion_platillo.c.id_platillo == id_platillo).all()
    return [dict(row._mapping) for row in stmt]


@platillos.get("/platillo/get_all_platillos")
def get_all_platillos(db: Session = Depends(get_db)):
    # Obtener todos los platillos
    query = db.query(platillo).all()
    platillos_lista = []

    for row in query:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            # ✅ Agregamos las claves al diccionario, no con append
            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo")
def get_platillo(Nombre_platillo: str, db: Session = Depends(get_db)):
    stmt = select(platillo).where(platillo.c.Nombre_platillo.ilike(f"%{Nombre_platillo}%"))
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            # ✅ Agregamos las claves al diccionario, no con append
            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista


@platillos.get("/platillo/get_platillo_id")
def get_platillo(id: str, db: Session = Depends(get_db)):
    stmt = (
        select(
            platillo.c.id_platillo,
            platillo.c.Nombre_platillo,
            platillo.c.Ruta_imagen,
            platillo.c.precio_venta,
            platillo.c.Descripcion,
            tipo_platillo.c.descripcion,
            tipo_platillo.c.color
        )
        .select_from(platillo.join(tipo_platillo, platillo.c.id_tipo_platillo == tipo_platillo.c.id_tipo_platillo))
        .where(platillo.c.id_platillo == id)
    )
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            # ✅ Agregamos las claves al diccionario, no con append
            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista

@platillos.get("/platillo/get_platillo_by_tipo", summary="Obtener los platillos por categoria")
def get_platillo_by_tipo(id_tipo_platillo: int, db: Session = Depends(get_db)):
    stmt = select(platillo).where(platillo.c.id_tipo_platillo == id_tipo_platillo)
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            # ✅ Agregamos las claves al diccionario, no con append
            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista

@platillos.get("/platillo/get_platillo_by_price", summary="Obtener por precio")
def get_platillo_by_price(min_price: int, max_price: int, db:Session = Depends(get_db)):
    stmt = select(platillo).where(
        (platillo.c.precio_venta >= min_price) & (platillo.c.precio_venta <= max_price)
    )
    plato = db.execute(stmt).all()
    platillos_lista = []

    for row in plato:
        data = dict(row._mapping)
        id_platillo = data["id_platillo"]

        # Buscar la oferta más alta vigente para este platillo
        stmt_oferta = (
            select(func.max(ofertas.c.porcentaje_descuento))
            .select_from(ofertas.join(oferta_platillos, ofertas.c.id_oferta == oferta_platillos.c.id_oferta))
            .where(
                and_(
                    oferta_platillos.c.id_platillo == id_platillo,
                    ofertas.c.activo == True,
                    ofertas.c.fecha_inicio <= func.now(),
                    ofertas.c.fecha_fin >= func.now()
                )
            )
        )

        descuento = db.execute(stmt_oferta).scalar()

        # Si hay descuento, aplica el precio con descuento
        if descuento and float(descuento) > 0:
            precio_original = float(data["precio_venta"])
            precio_final = round(precio_original * (1 - float(descuento) / 100), 2)

            # ✅ Agregamos las claves al diccionario, no con append
            data["En_oferta"] = True
            data["Porcentaje_oferta"] = float(descuento)
            data["precio_original"] = precio_original
            data["precio_venta"] = precio_final

        else:
            data["En_oferta"] = False
            data["precio_venta"] = float(data["precio_venta"])

        platillos_lista.append(data)

    return platillos_lista

@platillos.put("/platillo/update_platillo/{id}")
def update_platillo(id_platillo: str, data: dict = Body(...), db: Session = Depends(get_db)):
    stmt = (
        update(platillo)
        .where(platillo.c.id_platillo == id_platillo)
        .values(**data)
    )
    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Platillo no encontrado")
    return {"message": "Platillo actualizado correctamente"}



@platillos.put("/platillo/update_options_platillo", summary="Actualizar una opción de personalización de un platillo")
def update_option_platillo(id_option: str, data_option: dict = Body(...), db: Session = Depends(get_db)):
    try:

        if "opcion" in data_option:
            # ✅ Verificar si ya existe otra opción con el mismo nombre en el mismo platillo
            stmt_check = select(opcion_platillo).where(
                (opcion_platillo.c.opcion == data_option["opcion"]) &
                (opcion_platillo.c.id_platillo == data_option["id_platillo"]) &
                (opcion_platillo.c.id_option != id_option)
            )

            existe_option = db.execute(stmt_check).fetchone()

            if existe_option:
                raise HTTPException(status_code=400, detail="Ya existe una opción con ese nombre para este platillo")

        # ✅ Actualizar la opción
        stmt_update = (
            update(opcion_platillo)
            .where(opcion_platillo.c.id_option == id_option)
            .values(**data_option)
        )

        result = db.execute(stmt_update)
        db.commit()

        # ✅ Verificar si realmente se actualizó algo
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="No se encontró la opción especificada")

        return {
            "message": "Opción de personalización actualizada correctamente",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



@platillos.delete("/platillo/delete_option/{id_option}", summary="Eliminar una opción de personalización de un platillo")
def delete_option_platillo(id_option: str, db: Session = Depends(get_db)):
    try:
        # ✅ Verificar si la opción existe antes de eliminarla
        stmt_check = select(opcion_platillo).where(opcion_platillo.c.id_option == id_option)
        option_existente = db.execute(stmt_check).fetchone()

        if not option_existente:
            raise HTTPException(status_code=404, detail="No se encontró la opción especificada")

        # ✅ Eliminar la opción
        stmt_delete = delete(opcion_platillo).where(opcion_platillo.c.id_option == id_option)
        db.execute(stmt_delete)
        db.commit()

        return {
            "message": "Opción de personalización eliminada correctamente",
            "id_opcion": id_option
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))