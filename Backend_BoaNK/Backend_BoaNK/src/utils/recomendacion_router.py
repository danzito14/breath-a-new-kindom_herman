from fastapi import APIRouter
from src.utils.recomendaciones import recomendar_top3_global

router_recomendar = APIRouter()

@router_recomendar.get("/recomendar/global", summary="Recomendar los 3 mejores platillos (TOPSIS Global)")
def recomendar_global():

    try:
        recomendaciones = recomendar_top3_global()

        return {
            "status": "success",
            "message": "Top 3 platillos recomendados",
            "data": recomendaciones
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
