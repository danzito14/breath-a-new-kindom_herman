import numpy as np
from sqlalchemy import select
from src.core.db_credentials import engine
from src.db.model.pedidos.pedidos_model import detalle_pedido
from src.db.model.platillo_model import platillo  # Importa tu tabla correctamente


def recomendar_top3_global():

    with engine.connect() as conn:

        # ===============================
        #   OBTENER HISTORIAL DE PEDIDOS
        # ===============================
        query = select(
            detalle_pedido.c.id_platillo,
            detalle_pedido.c.tiempo_total,
            detalle_pedido.c.Precio_unitario,
            detalle_pedido.c.estado,
        )

        rows = conn.execute(query).fetchall()

    if not rows:
        return []

    # ===============================
    #   AGRUPAR DATOS
    # ===============================
    data = {}

    for row in rows:
        pid = row.id_platillo

        if pid not in data:
            data[pid] = {
                "tiempos": [],
                "precios": [],
                "cancelados": 0,
                "total": 0
            }

        data[pid]["tiempos"].append(row.tiempo_total)
        data[pid]["precios"].append(float(row.Precio_unitario))
        data[pid]["total"] += 1

        if row.estado == "cancelado":
            data[pid]["cancelados"] += 1

    plat_ids = list(data.keys())
    matriz = []

    for pid in plat_ids:
        d = data[pid]
        cancel_rate = d["cancelados"] / d["total"] if d["total"] > 0 else 0

        matriz.append([
            d["total"],                 # popularidad
            np.mean(d["tiempos"]),      # tiempo
            np.mean(d["precios"]),      # precio
            cancel_rate                 # cancelación
        ])

    matriz = np.array(matriz)

    # ===============================
    #   TOPSIS
    # ===============================
    pesos = np.array([0.40, 0.25, 0.15, 0.20])
    beneficio = np.array([1, 0, 0, 0])

    norm = matriz / np.sqrt((matriz ** 2).sum(axis=0))
    ponderada = norm * pesos

    ideal_pos = np.where(beneficio == 1, ponderada.max(axis=0), ponderada.min(axis=0))
    ideal_neg = np.where(beneficio == 1, ponderada.min(axis=0), ponderada.max(axis=0))

    d_pos = np.sqrt(((ponderada - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((ponderada - ideal_neg) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)

    # ===============================
    #   OBTENER TOP 3
    # ===============================
    top3_idx = np.argsort(score)[::-1][:5]
    top3_ids = [plat_ids[i] for i in top3_idx]

    # ===============================
    #   OBTENER INFO COMPLETA
    # ===============================

    with engine.connect() as conn:
        query = select(platillo).where(platillo.c.id_platillo.in_(top3_ids))
        result = conn.execute(query).fetchall()

    # Convertir rows a diccionario
    platillos_info = [
        dict(row._mapping) for row in result
    ]

    return platillos_info
