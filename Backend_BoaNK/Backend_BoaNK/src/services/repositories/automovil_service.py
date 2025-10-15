import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert,select, update

from src.db.model.automovil_model import automovil
from src.schemas.automovil_schema import AutomovilSchema
from src.core.db_credentials import get_db

class AutomovilService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_automovil(self, data_automovil: AutomovilSchema):
        automovil_dict = data_automovil.dict(exclude_unset=True)

        existe = self.db.execute(
            select(automovil).where(automovil.c.apodo == automovil_dict["apodo"])
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail=f"{automovil_dict['apodo']} ya existe")

        automovil_dict["id_auto"] = str(uuid.uuid4())
        stmt = insert(automovil).values(**automovil_dict)
        try:
            self.db.execute(stmt)
            self.db.commit()
            return {"message": f"El automovil {automovil_dict['apodo']} agregado correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def get_all_automovil(self):
        try:
            query = self.db.query(automovil).all()
            return  [dict(row._mapping) for row in query]
        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def get_automovil(self, apodo:str):
        try:
            stmt = select(automovil).where(automovil.c.apodo.ilike(f"%{apodo}%"))
            automovil_ = self.db.execute(stmt).first()

            if not automovil_:
              raise HTTPException(status_code=400, detail="Automovil no encontrado")
            return dict(automovil_._mapping)

        except Exception as e:
            raise  HTTPException(status_code=400, detail=str(e))

    def update_automovil (self, id_automovil:str, data:dict):
        try:
            # checamos que no tenga el apodo repetido
            if "apodo" in data:
                existe = self.db.execute(
                    select(automovil).where(automovil.c.apodo == data['apodo'])
                    .where(automovil.c.id_auto != id_automovil)
                ).first()

                if existe:
                    raise  HTTPException(status_code=400, detail=f"{data['apodo']} ya existe")

            stmt = (update(automovil).where(automovil.c.id_auto == id_automovil).values(**data))

            result = self.db.execute(stmt)
            self.db.commit()

            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="No se pudo actualizar los datos de automovil")

            return {"message": "Datos actualizados correctamente"}
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
