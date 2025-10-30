import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.email_sender = os.getenv("EMAIL_SENDER")
        self.email_password = os.getenv("EMAIL_PASSWORD")

    def enviar_correo(self, destinatario: str, asunto: str, nombre_usuario: str, codigo: str):
        try:
            if not all([self.email_sender, self.email_password]):
                raise ValueError("❌ Faltan variables de entorno EMAIL_SENDER o EMAIL_PASSWORD")

            message = MIMEMultipart("alternative")
            message["Subject"] = asunto
            message["From"] = self.email_sender
            message["To"] = destinatario

            texto = f"""
            Hola {nombre_usuario},

            Tu registro en Breath of a New Kingdom fue exitoso.
            ¡Gracias por unirte a nosotros!

            Tu código de activación es: {codigo}
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
                <h2>Hola {nombre_usuario},</h2>
                <p>Gracias por registrarte en <b>Breath of a New Kingdom</b>.</p>
                <p>Tu código de activación es: <b>{codigo}</b></p>
                <p>El código expirará en 10 minutos.</p>

                <a class="iniciar-sesion" href="http://localhost:8000/cuenta/activar_cuenta?correo={destinatario}&codigo={codigo}">
                    Activar cuenta
                </a>
            </body>
            </html>
            """

            message.attach(MIMEText(texto, "plain"))
            message.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(message)

            logger.info(f"✅ Correo enviado a {destinatario}")

        except Exception as e:
            logger.exception(f"❌ Error al enviar correo: {e}")
            print(str(e))
