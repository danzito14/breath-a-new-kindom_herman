from fastapi import APIRouter, HTTPException
from src.utils.recomendaciones import recomendar_top5_mes, recomendar_top5_semana

router_recomendar = APIRouter()


"""
def recomendar_mes():
    Retorna el top 5 de platillos del mes actual usando TOPSIS
    try:
        recomendaciones = recomendar_top5_mes()

        if not recomendaciones:
            return {
                "status": "success",
                "message": "No hay datos suficientes para generar recomendaciones del mes",
                "data": []
            }

        return {
            "status": "success",
            "message": f"Top {len(recomendaciones)} platillos del mes",
            "data": recomendaciones
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_recomendar.get("/recomendar/semana", summary="Recomendar los 5 mejores platillos de la semana")
"""
@router_recomendar.get("/recomendar/global", summary="Recomendar los 5 mejores platillos (TOPSIS Global)")

def recomendar_semana():
    """
    Retorna el top 5 de platillos de la semana actual usando TOPSIS
    """
    try:
        recomendaciones = recomendar_top5_semana()

        if not recomendaciones:
            return {
                "status": "success",
                "message": "No hay datos suficientes para generar recomendaciones de la semana",
                "data": []
            }

        return {
            "status": "success",
            "message": f"Top {len(recomendaciones)} platillos de la semana",
            "data": recomendaciones
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))