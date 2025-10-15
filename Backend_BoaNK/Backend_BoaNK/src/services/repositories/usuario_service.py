from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import insert, select
import uuid

from src.schemas.user_schema import UserSchema
from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UsuarioService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_user(self, *args, **kwargs):
        datos_requeridos = {
            "id_usuario",
            "id_nvl_usuario",
            "Nickname",
            "Contraseña",
            "Nombre",
            "Apellido",
            "Correo_electronico",
            "Num_telefonico",
            "Ruta_imagen",
            "estatus"
        }

        # Si llegan desde el router (objeto UserSchema)
        if args and isinstance(args[0], UserSchema):
            data_user = args[0]
            user_dict = data_user.dict(exclude_unset=True)

            # Generar id_usuario si no viene incluido
            if "id_usuario" not in user_dict:
                user_dict["id_usuario"] = str(uuid.uuid4())

        # Si llegan desde empleados con kwargs
        elif kwargs:
            missing = datos_requeridos - kwargs.keys()
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Faltan los siguientes datos: {', '.join(missing)}"
                )

            extra = kwargs.keys() - datos_requeridos - {"id_usuario"}
            if extra:
                raise HTTPException(
                    status_code=400,
                    detail=f"Datos desconocidos o no esperados: {', '.join(extra)}"
                )

            # ✅ Generar id_usuario si no se proporciona
            if "id_usuario" not in kwargs:
                kwargs["id_usuario"] = str(uuid.uuid4())

            data_user = UserSchema(**kwargs)
            user_dict = data_user.dict(exclude_unset=True)

        else:
            raise HTTPException(status_code=400, detail="No se recibió ningún dato")

        # Validar correo único
        existing_correo = self.db.execute(
            select(usuarios).where(usuarios.c.Correo_electronico == data_user.Correo_electronico)
        ).first()
        if existing_correo:
            raise HTTPException(status_code=400, detail="Correo electrónico ya registrado")

        # Validar nickname único
        existing_user = self.db.execute(
            select(usuarios).where(usuarios.c.Nickname == data_user.Nickname)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Nickname ya existente")

        # Hashear contraseña
        user_dict["Contraseña"] = pwd_context.hash(data_user.Contraseña)

        stmt = insert(usuarios).values(**user_dict)

        try:
            self.db.execute(stmt)
            self.db.commit()
            return {
                "message": "Usuario creado correctamente",
                "nombre": user_dict["Nombre"],
                "id_usuario": user_dict["id_usuario"]
            }
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=str(e))
