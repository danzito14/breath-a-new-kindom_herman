from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy import insert, select
import uuid

from src.schemas.user_schema import UserSchema
from src.db.model.usuario_model import usuarios
from src.core.db_credentials import get_db
from src.services.system.email.activar_cuenta_service import activar_cuentaService
from src.services.system.email.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsuarioService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_user(self, *args, background_tasks: BackgroundTasks = None, **kwargs):
        datos_requeridos = {
            "id_usuario", "id_nvl_usuario", "Nickname", "Contraseña", "Nombre",
            "Apellido", "Correo_electronico", "Num_telefonico", "Ruta_imagen", "estatus"
        }

        # Si llega un esquema (desde el router)
        if args and isinstance(args[0], UserSchema):
            data_user = args[0]
            user_dict = data_user.dict(exclude_unset=True)

            if "id_usuario" not in user_dict:
                user_dict["id_usuario"] = str(uuid.uuid4())

        # Si llega por kwargs (desde otra función)
        elif kwargs:
            missing = datos_requeridos - kwargs.keys()
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Faltan los siguientes datos: {', '.join(missing)}"
                )

            if "id_usuario" not in kwargs:
                kwargs["id_usuario"] = str(uuid.uuid4())

            data_user = UserSchema(**kwargs)
            user_dict = data_user.dict(exclude_unset=True)

        else:
            raise HTTPException(status_code=400, detail="No se recibió ningún dato")

        # Verificar si el correo o nickname ya existen
        if (user_dict["id_nvl_usuario"] != 8):
            print("entro a la funcion")
            if self.db.execute(
                    select(usuarios).where(usuarios.c.Correo_electronico == user_dict["Correo_electronico"])).first():
                raise HTTPException(status_code=400, detail="Correo electrónico ya registrado")
        else:
            print(user_dict["id_nvl_usuario"])
            print(user_dict["Correo_electronico"])

        if self.db.execute(select(usuarios).where(usuarios.c.Nickname == user_dict["Nickname"])).first():
            raise HTTPException(status_code=400, detail="Nickname ya existente")

        # Hashear la contraseña
        user_dict["Contraseña"] = pwd_context.hash(user_dict["Contraseña"])

        stmt = insert(usuarios).values(**user_dict)

        try:
            self.db.execute(stmt)
            self.db.commit()

            # Si es un usuario normal (nivel 1)
            if user_dict.get("id_nvl_usuario") == 1:
                codigo_activacion = str(uuid.uuid4())[:6].upper()

                activar_service = activar_cuentaService(self.db)
                activar_service.create_codigo(
                    correo_electronico=user_dict["Correo_electronico"],
                    codigo=codigo_activacion,
                    create_at=datetime.utcnow(),
                    expira_at=datetime.utcnow() + timedelta(minutes=10)
                )

                email_service = EmailService()

                texto = f"""
                            Hola {user_dict["Nickname"]},

                            Tu registro en Breath of a New Kingdom fue exitoso.
                            ¡Gracias por unirte a nosotros!

                            Tu código de activación es: {codigo_activacion}
                            Expira en 10 minutos.
                            """

                html = f"""
                            <html>
                            <head>
                                <style>
                                    .iniciar-sesion {{
                                        background-color: #D0AF43;
                                        border: none;
                                        border-radius: 10px;
                                        padding: 10px 20px;
                                        color: white;
                                        font-size: 18px;
                                        text-decoration: none;
                                        display: inline-block;
                                    }}
                                </style>
                            </head>
                            <body>
                                <h2>Hola {user_dict["Nickname"]},</h2>
                                <p>Gracias por registrarte en <b>Breath of a New Kingdom</b>.</p>
                                <p>Tu código de activación es: <b>{codigo_activacion}</b></p>
                                <p>El código expirará en 10 minutos.</p>

                                <a class="iniciar-sesion" href="http://localhost:8000/cuenta/activar_cuenta?correo={user_dict["Correo_electronico"]}&codigo={codigo_activacion}">
                                    Activar cuenta
                                </a>
                            </body>
                            </html>
                            """

                # ✅ Enviar correo en segundo plano
                if background_tasks:
                    background_tasks.add_task(
                        email_service.enviar_correo,
                        destinatario=user_dict["Correo_electronico"],
                        asunto="Activa tu cuenta - Breath of a New Kingdom",
                        texto=texto,
                        html = html
                    )
                else:
                    # Si no hay BackgroundTasks (por ejemplo, en pruebas)
                    email_service.enviar_correo(
                        destinatario=user_dict["Correo_electronico"],
                        asunto="Activa tu cuenta - Breath of a New Kingdom",
                        texto=texto,
                        html=html
                    )

            return {
                "message": "Usuario creado correctamente. Verifica tu correo para activarlo.",
                "nombre": user_dict["Nombre"],
                "id_usuario": user_dict["id_usuario"]
            }

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear usuario: {e}")
