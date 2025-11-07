from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.core.db_credentials import get_db
from src.core.jwt_managger import get_current_user

untils_empleados = APIRouter(prefix="/untils_empleados", tags=["Untils empleados"])

@untils_empleados.get("/get_nombre_empleado", summary="Buscar el rol y el nombre del chameador")
def get_vista_puesto_empledo(current_user: str = Depends(get_current_user), db: Session = Depends(get_db) ):
   try:
        """
            End point para buscar como se llaman nuestros cambeadores
        """
        stmt = text("SELECT * FROM vista_rol_empleado_usuario WHERE id_usuario = :id_usuario")
        resultado = db.execute(stmt, {"id_usuario": current_user}).mappings().first()

        if not resultado:
            raise HTTPException(status_code=404, detail="Empleado no encontrado")

        return dict(resultado)

   except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
