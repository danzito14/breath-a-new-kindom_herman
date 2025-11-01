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

    def enviar_correo(self, destinatario: str, asunto: str, texto:str, html:str):
        try:
            if not all([self.email_sender, self.email_password]):
                raise ValueError("❌ Faltan variables de entorno EMAIL_SENDER o EMAIL_PASSWORD")

            message = MIMEMultipart("alternative")
            message["Subject"] = asunto
            message["From"] = self.email_sender
            message["To"] = destinatario

            texto = texto
            html = html

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
