from fastapi import FastAPI
from src.routers.usuario_router import user



app = FastAPI()

app.include_router(user)
