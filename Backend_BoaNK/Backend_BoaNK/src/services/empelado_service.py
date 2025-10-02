import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import insert, select
import string, random

from src.core.db_credentials import get_db

from src.db.model.usuario_model import usuarios
from src.db.model.empleado_model import empleado
from src.db.model.puesto_model import puesto

from src.schemas.empleados_schema import EmpleadosSchema
from src.services.usuario_service import UsuarioService

class EmpleadoService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_empleado(self, data_empleado: EmpleadosSchema):
        # Convertir Pydantic en diccionario
        empleado_dict = data_empleado.dict(exclude_unset=True)

        service_user = UsuarioService(self.db)
        nvl_usuario = self.obtener_nvl_usuario(empleado_dict["id_puesto"])
        nickname = self.generar_nickname(empleado_dict["Nombre"], empleado_dict["Apellido"], empleado_dict["id_puesto"])
        contraseña = self.crear_contraseña()

        datos_usuario = service_user.create_user(
            id_nvl_usuario=nvl_usuario,
            Nickname=nickname,
            Contraseña=contraseña,
            Nombre=empleado_dict.get("Nombre"),
            Apellido=empleado_dict.get("Apellido"),
            Correo_electronico=empleado_dict.get("Correo_electronico"),
            Num_telefonico=empleado_dict.get("Num_telefonico"),
            Ruta_imagen=empleado_dict.get("Ruta_imagen"),
            estatus=empleado_dict.get("estatus")
        )

        id_usuario = datos_usuario["id_usuario"]

        # Asociar el usuario con el empleado
        empleado_dict["id_empleado"] = str(uuid.uuid4())
        empleado_dict["id_usuario"] = id_usuario

        # Crear sentencia INSERT
        stmt = insert(empleado).values(**empleado_dict)

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {
                "message": "Empleado registrado correctamente",
                "nombre": empleado_dict["Nombre"],
                "usuario": nickname,
                "contraseña": contraseña
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

    def obtener_nvl_usuario(self, id_puesto):
        nlv_usuario = self.db.execute(
            select(puesto.c.id_nvl_usuario).where(puesto.c.id_puesto == id_puesto)
        ).first()

        return nlv_usuario[0] if nlv_usuario else None

    def generar_nickname(self, nombre, apellido, id_puesto):
        iniciales = nombre[0].upper() + apellido[0].upper()
        apellido_capitalizado = apellido.capitalize()
        return f"{iniciales}{apellido_capitalizado}{id_puesto}"

    def crear_contraseña(self, length=8):
        caracteres = string.ascii_lowercase + string.digits
        return ''.join(random.choice(caracteres) for _ in range(length))
