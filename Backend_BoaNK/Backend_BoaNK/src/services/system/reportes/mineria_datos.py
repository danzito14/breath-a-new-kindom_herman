from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import json
from src.core.db_credentials import get_db

mineria = APIRouter(prefix="/mineria", tags=["Minería de Datos"])

# CONSTANTE: Siempre usar los últimos 30 días
DIAS_ANALISIS = 30


async def get_data_for_mining(db: AsyncSession):
    """
    Obtiene datos históricos de los últimos 30 días para análisis
    """
    query = text("""
        SELECT 
            dp.id_detalle,
            dp.id_pedido,
            dp.id_platillo,
            pl.Nombre_platillo,
            COALESCE(tp.descripcion, 'Sin categoría') as Categoria,
            pl.precio_venta,
            pl.precio_produccion,
            1 as Cantidad,
            dp.Precio_unitario,
            dp.estado as estado_platillo,
            p.Fecha,
            p.Estado as estado_pedido,
            p.Tipo_pedido,
            p.total as total_pedido,
            HOUR(p.Fecha) as hora_pedido,
            DAYOFWEEK(p.Fecha) as dia_semana,
            DAY(p.Fecha) as dia_mes,
            CASE 
                WHEN dp.estado = 'cancelado' THEN 1
                ELSE 0
            END as fue_cancelado
        FROM detalle_pedido dp
        INNER JOIN platillo pl ON dp.id_platillo = pl.id_platillo
        LEFT JOIN tipo_platillo tp ON pl.id_tipo_platillo = tp.id_tipo_platillo
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        WHERE p.Fecha >= DATE_SUB(CURDATE(), INTERVAL :days DAY)
        ORDER BY p.Fecha DESC
    """)

    # Ejecutar la query de forma asíncrona
    result =  db.execute(query, {"days": DIAS_ANALISIS})

    # mappings().all() es síncrono, no necesita await
    rows = result.mappings().all()

    # Convertir a DataFrame
    data = []
    for row in rows:
        row_dict = dict(row)
        # Convertir Decimal a float y datetime a string
        for key, value in row_dict.items():
            if isinstance(value, Decimal):
                row_dict[key] = float(value)
            elif isinstance(value, datetime):
                row_dict[key] = value
        data.append(row_dict)

    return pd.DataFrame(data)


@mineria.get("/prediccion-cancelaciones")
async def predecir_cancelaciones(db: AsyncSession = Depends(get_db)):
    """
    Predice qué platillos tienen mayor probabilidad de ser cancelados
    basándose en patrones históricos de los últimos 30 días
    """
    try:
        # Obtener datos de los últimos 30 días
        df = await get_data_for_mining(db)

        if len(df) < 50:
            return {
                "error": "No hay suficientes datos históricos en los últimos 30 días",
                "predicciones": [],
                "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
                "accuracy_modelo": 0,
                "total_datos_analizados": len(df),
                "factores_importantes": {},
                "recomendaciones": []
            }

        # Preparar características para el modelo
        features = pd.DataFrame()
        features['precio_venta'] = df['precio_venta']
        features['precio_produccion'] = df['precio_produccion']
        features['margen'] = (df['precio_venta'] - df['precio_produccion']) / df['precio_venta']
        features['cantidad'] = df['Cantidad']
        features['hora_pedido'] = df['hora_pedido']
        features['dia_semana'] = df['dia_semana']
        features['total_pedido'] = df['total_pedido']

        # Codificar variables categóricas
        le_categoria = LabelEncoder()
        le_tipo = LabelEncoder()

        features['categoria_encoded'] = le_categoria.fit_transform(df['Categoria'])
        features['tipo_pedido_encoded'] = le_tipo.fit_transform(df['Tipo_pedido'])

        # Variable objetivo
        y = df['fue_cancelado']

        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            features, y, test_size=0.2, random_state=42
        )

        # Entrenar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Calcular accuracy
        accuracy = model.score(X_test, y_test)

        # Obtener platillos únicos y calcular riesgo
        platillos_unicos = df.groupby('Nombre_platillo').agg({
            'fue_cancelado': 'mean',
            'id_platillo': 'first',
            'Categoria': 'first',
            'precio_venta': 'mean',
            'precio_produccion': 'mean'
        }).reset_index()

        platillos_unicos['tasa_cancelacion'] = platillos_unicos['fue_cancelado'] * 100

        # Calcular importancia de características
        feature_importance = dict(zip(
            features.columns,
            model.feature_importances_
        ))

        # Ordenar por tasa de cancelación
        platillos_riesgo = platillos_unicos.nlargest(10, 'tasa_cancelacion')

        predicciones = []
        for _, row in platillos_riesgo.iterrows():
            predicciones.append({
                "platillo": row['Nombre_platillo'],
                "categoria": row['Categoria'],
                "tasa_cancelacion": round(float(row['tasa_cancelacion']), 2),
                "precio_venta": round(float(row['precio_venta']), 2),
                "nivel_riesgo": "Alto" if row['tasa_cancelacion'] > 15 else "Medio" if row[
                                                                                           'tasa_cancelacion'] > 8 else "Bajo"
            })

        return {
            "accuracy_modelo": round(accuracy * 100, 2),
            "total_datos_analizados": len(df),
            "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
            "predicciones": predicciones,
            "factores_importantes": {
                k: round(float(v) * 100, 2)
                for k, v in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "recomendaciones": generar_recomendaciones(predicciones)
        }

    except Exception as e:
        raise HTTPException(500, f"Error en predicción: {str(e)}")


@mineria.get("/patrones-temporales")
async def analizar_patrones_temporales(db: AsyncSession = Depends(get_db)):
    """
    Analiza patrones de ventas por hora y día de los últimos 30 días
    """
    try:
        df = await get_data_for_mining(db)

        if len(df) == 0:
            return {
                "error": "No hay datos disponibles en los últimos 30 días",
                "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
                "ventas_por_hora": [],
                "ventas_por_dia_semana": [],
                "horas_pico": [],
                "horas_bajas": [],
                "insights": []
            }

        # Análisis por hora del día
        ventas_por_hora = df.groupby('hora_pedido').agg({
            'id_detalle': 'count',
            'Precio_unitario': 'sum',
            'fue_cancelado': 'mean'
        }).reset_index()

        ventas_por_hora.columns = ['hora', 'cantidad_pedidos', 'ingresos', 'tasa_cancelacion']

        # Análisis por día de la semana
        dias_nombres = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        ventas_por_dia = df.groupby('dia_semana').agg({
            'id_detalle': 'count',
            'Precio_unitario': 'sum',
            'fue_cancelado': 'mean'
        }).reset_index()

        ventas_por_dia['dia_nombre'] = ventas_por_dia['dia_semana'].map(
            lambda x: dias_nombres[x - 1] if 1 <= x <= 7 else 'Desconocido'
        )

        # Identificar horas pico
        hora_pico = ventas_por_hora.nlargest(3, 'cantidad_pedidos')
        horas_bajas = ventas_por_hora.nsmallest(3, 'cantidad_pedidos')

        return {
            "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
            "ventas_por_hora": [
                {
                    "hora": f"{int(row['hora'])}:00",
                    "pedidos": int(row['cantidad_pedidos']),
                    "ingresos": round(float(row['ingresos']), 2),
                    "tasa_cancelacion": round(float(row['tasa_cancelacion']) * 100, 2)
                }
                for _, row in ventas_por_hora.iterrows()
            ],
            "ventas_por_dia_semana": [
                {
                    "dia": row['dia_nombre'],
                    "pedidos": int(row['id_detalle']),
                    "ingresos": round(float(row['Precio_unitario']), 2),
                    "tasa_cancelacion": round(float(row['fue_cancelado']) * 100, 2)
                }
                for _, row in ventas_por_dia.iterrows()
            ],
            "horas_pico": [
                {
                    "hora": f"{int(row['hora'])}:00",
                    "pedidos": int(row['cantidad_pedidos'])
                }
                for _, row in hora_pico.iterrows()
            ],
            "horas_bajas": [
                {
                    "hora": f"{int(row['hora'])}:00",
                    "pedidos": int(row['cantidad_pedidos'])
                }
                for _, row in horas_bajas.iterrows()
            ],
            "insights": generar_insights_temporales(ventas_por_hora, ventas_por_dia)
        }

    except Exception as e:
        raise HTTPException(500, f"Error en análisis temporal: {str(e)}")


@mineria.get("/prediccion-demanda")
async def predecir_demanda(db: AsyncSession = Depends(get_db)):
    """
    Predice la demanda futura de platillos basándose en tendencias de los últimos 30 días
    """
    try:
        df = await get_data_for_mining(db)

        if len(df) == 0:
            return {
                "error": "No hay datos disponibles en los últimos 30 días",
                "periodo_datos": f"Últimos {DIAS_ANALISIS} días",
                "fecha_analisis": datetime.now().strftime("%Y-%m-%d"),
                "predicciones": [],
                "recomendaciones_inventario": []
            }

        # Agrupar por platillo y fecha
        demanda_diaria = df.groupby(['Nombre_platillo', df['Fecha'].dt.date]).agg({
            'Cantidad': 'sum'
        }).reset_index()

        predicciones_platillos = []

        # Analizar cada platillo (top 15)
        for platillo in df['Nombre_platillo'].unique()[:15]:
            datos_platillo = demanda_diaria[demanda_diaria['Nombre_platillo'] == platillo]

            if len(datos_platillo) < 5:  # Ajustado para 30 días
                continue

            # Calcular tendencia
            cantidades = datos_platillo['Cantidad'].values
            # Usar últimos 7 días para comparación
            dias_disponibles = min(7, len(cantidades))
            promedio_semanal = np.mean(cantidades[-dias_disponibles:])
            promedio_total = np.mean(cantidades)
            tendencia = ((promedio_semanal - promedio_total) / promedio_total * 100) if promedio_total > 0 else 0

            # Predicción simple para próxima semana
            prediccion = promedio_semanal * (1 + tendencia / 100)

            predicciones_platillos.append({
                "platillo": platillo,
                "demanda_promedio_diaria": round(float(promedio_total), 2),
                "demanda_ultima_semana": round(float(promedio_semanal), 2),
                "prediccion_proxima_semana": round(float(prediccion), 2),
                "tendencia": round(float(tendencia), 2),
                "estado_tendencia": "Creciente" if tendencia > 5 else "Estable" if tendencia > -5 else "Decreciente"
            })

        # Ordenar por demanda predicha
        predicciones_platillos.sort(key=lambda x: x['prediccion_proxima_semana'], reverse=True)

        return {
            "fecha_analisis": datetime.now().strftime("%Y-%m-%d"),
            "periodo_datos": f"Últimos {DIAS_ANALISIS} días",
            "predicciones": predicciones_platillos[:10],
            "recomendaciones_inventario": generar_recomendaciones_inventario(predicciones_platillos)
        }

    except Exception as e:
        raise HTTPException(500, f"Error en predicción de demanda: {str(e)}")


@mineria.get("/analisis-rentabilidad")
async def analizar_rentabilidad_avanzada(db: AsyncSession = Depends(get_db)):
    """
    Análisis avanzado de rentabilidad de los últimos 30 días
    """
    try:
        df = await get_data_for_mining(db)

        if len(df) == 0:
            return {
                "error": "No hay datos disponibles en los últimos 30 días",
                "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
                "top_rentables": [],
                "bajo_rendimiento": [],
                "por_categoria": [],
                "recomendaciones": []
            }

        # Análisis por platillo
        rentabilidad_platillo = df.groupby('Nombre_platillo').agg({
            'Cantidad': 'sum',
            'precio_venta': 'mean',
            'precio_produccion': 'mean',
            'Precio_unitario': 'sum',
            'fue_cancelado': 'mean'
        }).reset_index()

        rentabilidad_platillo['ganancia_total'] = (
                                                          rentabilidad_platillo['precio_venta'] - rentabilidad_platillo[
                                                      'precio_produccion']
                                                  ) * rentabilidad_platillo['Cantidad']

        rentabilidad_platillo['margen_porcentaje'] = (
                (rentabilidad_platillo['precio_venta'] - rentabilidad_platillo['precio_produccion']) /
                rentabilidad_platillo['precio_venta'] * 100
        )

        rentabilidad_platillo['roi'] = (
                rentabilidad_platillo['ganancia_total'] /
                (rentabilidad_platillo['precio_produccion'] * rentabilidad_platillo['Cantidad']) * 100
        )

        # Análisis por categoría
        rentabilidad_categoria = df.groupby('Categoria').agg({
            'Cantidad': 'sum',
            'precio_venta': 'mean',
            'precio_produccion': 'mean',
            'fue_cancelado': 'mean'
        }).reset_index()

        rentabilidad_categoria['margen'] = (
                (rentabilidad_categoria['precio_venta'] - rentabilidad_categoria['precio_produccion']) /
                rentabilidad_categoria['precio_venta'] * 100
        )

        # Top platillos más rentables
        top_rentables = rentabilidad_platillo.nlargest(10, 'ganancia_total')

        # Platillos de bajo rendimiento
        bajo_rendimiento = rentabilidad_platillo[
            (rentabilidad_platillo['margen_porcentaje'] < 30) |
            (rentabilidad_platillo['fue_cancelado'] > 0.1)
            ].nsmallest(10, 'ganancia_total')

        return {
            "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
            "top_rentables": [
                {
                    "platillo": row['Nombre_platillo'],
                    "ventas_totales": int(row['Cantidad']),
                    "ganancia_total": round(float(row['ganancia_total']), 2),
                    "margen": round(float(row['margen_porcentaje']), 2),
                    "roi": round(float(row['roi']), 2)
                }
                for _, row in top_rentables.iterrows()
            ],
            "bajo_rendimiento": [
                {
                    "platillo": row['Nombre_platillo'],
                    "ventas_totales": int(row['Cantidad']),
                    "margen": round(float(row['margen_porcentaje']), 2),
                    "tasa_cancelacion": round(float(row['fue_cancelado']) * 100, 2),
                    "problema": "Bajo margen" if row['margen_porcentaje'] < 30 else "Alta cancelación"
                }
                for _, row in bajo_rendimiento.iterrows()
            ],
            "por_categoria": [
                {
                    "categoria": row['Categoria'],
                    "ventas": int(row['Cantidad']),
                    "margen_promedio": round(float(row['margen']), 2),
                    "tasa_cancelacion": round(float(row['fue_cancelado']) * 100, 2)
                }
                for _, row in rentabilidad_categoria.iterrows()
            ],
            "recomendaciones": generar_recomendaciones_rentabilidad(top_rentables, bajo_rendimiento)
        }

    except Exception as e:
        raise HTTPException(500, f"Error en análisis de rentabilidad: {str(e)}")


@mineria.get("/segmentacion-clientes")
async def segmentar_clientes(db: AsyncSession = Depends(get_db)):
    """
    Segmenta patrones de pedidos de los últimos 30 días
    """
    try:
        df = await get_data_for_mining(db)

        if len(df) == 0:
            return {
                "error": "No hay datos disponibles en los últimos 30 días",
                "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
                "resumen_por_tipo": [],
                "insights": []
            }

        # Análisis por tipo de pedido
        por_tipo = df.groupby('Tipo_pedido').agg({
            'id_pedido': 'nunique',
            'Precio_unitario': 'sum',
            'fue_cancelado': 'mean',
            'total_pedido': 'mean'
        }).reset_index()

        # Análisis de ticket promedio por tipo
        por_tipo['ticket_promedio'] = por_tipo['Precio_unitario'] / por_tipo['id_pedido']

        return {
            "periodo_analisis": f"Últimos {DIAS_ANALISIS} días",
            "resumen_por_tipo": [
                {
                    "tipo": row['Tipo_pedido'],
                    "total_pedidos": int(row['id_pedido']),
                    "ingresos_totales": round(float(row['Precio_unitario']), 2),
                    "ticket_promedio": round(float(row['ticket_promedio']), 2),
                    "tasa_cancelacion": round(float(row['fue_cancelado']) * 100, 2)
                }
                for _, row in por_tipo.iterrows()
            ],
            "insights": generar_insights_segmentacion(por_tipo, df)
        }

    except Exception as e:
        raise HTTPException(500, f"Error en segmentación: {str(e)}")


def generar_recomendaciones(predicciones):
    """Genera recomendaciones basadas en predicciones"""
    recomendaciones = []

    for pred in predicciones[:3]:
        if pred['nivel_riesgo'] == 'Alto':
            recomendaciones.append(
                f"{pred['platillo']}: Revisar tiempo de preparación y calidad"
            )

    return recomendaciones


def generar_insights_temporales(ventas_hora, ventas_dia):
    """Genera insights de patrones temporales"""
    insights = []

    # Hora con más cancelaciones
    if len(ventas_hora) > 0:
        hora_max_cancel = ventas_hora.nlargest(1, 'tasa_cancelacion')
        if not hora_max_cancel.empty:
            insights.append(
                f"Mayor tasa de cancelación en hora {int(hora_max_cancel.iloc[0]['hora'])}:00"
            )

    return insights


def generar_recomendaciones_inventario(predicciones):
    """Genera recomendaciones de inventario"""
    recomendaciones = []

    for pred in predicciones[:5]:
        if pred['estado_tendencia'] == 'Creciente':
            recomendaciones.append(
                f"Aumentar inventario de {pred['platillo']} (tendencia +{pred['tendencia']:.1f}%)"
            )

    return recomendaciones


def generar_recomendaciones_rentabilidad(top, bajo):
    """Genera recomendaciones de rentabilidad"""
    recomendaciones = []

    if len(top) > 0:
        # Usar 'Nombre_platillo' que es el nombre de la columna en el DataFrame
        platillos_top = [row['Nombre_platillo'] for _, row in top.head(3).iterrows()]
        recomendaciones.append(
            f"Promocionar platillos top: {', '.join(platillos_top)}"
        )

    if len(bajo) > 0:
        recomendaciones.append(
            f"Revisar costos de platillos de bajo rendimiento"
        )

    return recomendaciones


def generar_insights_segmentacion(por_tipo, df):
    """Genera insights de segmentación"""
    insights = []

    if len(por_tipo) > 1:
        tipo_mayor = por_tipo.nlargest(1, 'Precio_unitario').iloc[0]
        insights.append(
            f"El tipo '{tipo_mayor['Tipo_pedido']}' genera más ingresos en los últimos 30 días"
        )

    return insights