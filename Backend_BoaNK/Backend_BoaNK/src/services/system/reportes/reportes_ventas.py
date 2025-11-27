from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, date, timedelta
from decimal import Decimal
from src.core.db_credentials import get_db

reportes = APIRouter(prefix="/reportes", tags=["Reportes"])


async def fetch_aggregated_data(db: AsyncSession, query: str, params=None):
    """
    Ejecuta una consulta agregada y retorna los resultados en el formato esperado
    """
    result = db.execute(text(query), params or {})
    row = result.mappings().first()

    if not row:
        return {
            "platillos_preparados": 0,
            "platillos_cancelados": 0,
            "total_platillos": 0,
            "ingresos_estimados": 0.0,
            "egresos_estimados": 0.0,
            "ganancia_estimada": 0.0,
            "margen_ganancia": 0.0,
            "egresos_cancelados": 0.0,
            "ticket_promedio": 0.0,
            "tasa_cancelacion": 0.0,
            "platillos_por_pedido": 0.0,
            "total_pedidos": 0,
            "pedidos_completados": 0,
            "pedidos_cancelados": 0,
            "pedidos_locales": 0,
            "pedidos_domicilio": 0
        }

    # Convertir Decimal a float para JSON serialization
    result_dict = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            result_dict[key] = float(value)
        else:
            result_dict[key] = value

    return result_dict


# Query base EXTENDIDA para los reportes
BASE_QUERY = """
    SELECT 
        -- Contadores básicos
        COUNT(DISTINCT id_pedido) as total_pedidos,
        COUNT(DISTINCT CASE WHEN Estado IN ('Entregado', 'Pagada') THEN id_pedido END) as pedidos_completados,
        COUNT(DISTINCT CASE WHEN Estado = 'Cancelado' THEN id_pedido END) as pedidos_cancelados,
        COUNT(DISTINCT CASE WHEN Tipo_pedido = 'Local' THEN id_pedido END) as pedidos_locales,
        COUNT(DISTINCT CASE WHEN Tipo_pedido = 'Entrega' THEN id_pedido END) as pedidos_domicilio,

        -- Platillos preparados (completados exitosamente)
        COALESCE(SUM(platillos_completados), 0) as platillos_preparados,

        -- Platillos cancelados
        COALESCE(SUM(platillos_cancelados), 0) as platillos_cancelados,

        -- Total de platillos
        COALESCE(SUM(total_platillos), 0) as total_platillos,

        -- Ingresos solo de pedidos no cancelados
        COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
            THEN total_ingresos_platillos ELSE 0 END), 0) as ingresos_estimados,

        -- Egresos reales basados en precio de producción
        COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
            THEN total_egresos_platillos ELSE 0 END), 0) as egresos_estimados,

        -- Ganancia real (ingresos - egresos)
        COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
            THEN ganancia_bruta ELSE 0 END), 0) as ganancia_estimada,

        -- Margen de ganancia promedio
        CASE 
            WHEN SUM(CASE WHEN Estado != 'Cancelado' THEN total_ingresos_platillos ELSE 0 END) > 0
            THEN ROUND(
                (SUM(CASE WHEN Estado != 'Cancelado' THEN ganancia_bruta ELSE 0 END) / 
                 SUM(CASE WHEN Estado != 'Cancelado' THEN total_ingresos_platillos ELSE 0 END)) * 100, 
                2
            )
            ELSE 0
        END as margen_ganancia,

        -- Costos perdidos por cancelaciones (egresos de platillos cancelados)
        COALESCE(SUM(egresos_cancelados), 0) as egresos_cancelados,

        -- NUEVAS MÉTRICAS

        -- Ticket promedio (ingresos / pedidos completados)
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN Estado != 'Cancelado' THEN id_pedido END) > 0
            THEN ROUND(
                SUM(CASE WHEN Estado != 'Cancelado' THEN total_ingresos_platillos ELSE 0 END) / 
                COUNT(DISTINCT CASE WHEN Estado != 'Cancelado' THEN id_pedido END),
                2
            )
            ELSE 0
        END as ticket_promedio,

        -- Tasa de cancelación (% pedidos cancelados)
        CASE 
            WHEN COUNT(DISTINCT id_pedido) > 0
            THEN ROUND(
                (COUNT(DISTINCT CASE WHEN Estado = 'Cancelado' THEN id_pedido END) * 100.0) / 
                COUNT(DISTINCT id_pedido),
                2
            )
            ELSE 0
        END as tasa_cancelacion,

        -- Platillos por pedido promedio
        CASE 
            WHEN COUNT(DISTINCT CASE WHEN Estado != 'Cancelado' THEN id_pedido END) > 0
            THEN ROUND(
                SUM(CASE WHEN Estado != 'Cancelado' THEN total_platillos ELSE 0 END) * 1.0 / 
                COUNT(DISTINCT CASE WHEN Estado != 'Cancelado' THEN id_pedido END),
                2
            )
            ELSE 0
        END as platillos_por_pedido

    FROM view_reporte_ventas_detallado
"""


@reportes.get("/hoy")
async def ventas_hoy(db: AsyncSession = Depends(get_db)):
    query = BASE_QUERY + """
        WHERE DATE(Fecha) = CURDATE();
    """
    return await fetch_aggregated_data(db, query)


@reportes.get("/semana")
async def ventas_semana(db: AsyncSession = Depends(get_db)):
    query = BASE_QUERY + """
        WHERE YEARWEEK(Fecha, 1) = YEARWEEK(CURDATE(), 1);
    """
    return await fetch_aggregated_data(db, query)


@reportes.get("/mes")
async def ventas_mes(db: AsyncSession = Depends(get_db)):
    query = BASE_QUERY + """
        WHERE YEAR(Fecha) = YEAR(CURDATE())
        AND MONTH(Fecha) = MONTH(CURDATE());
    """
    return await fetch_aggregated_data(db, query)


@reportes.get("/intervalo")
async def ventas_intervalo(inicio: date, fin: date, db: AsyncSession = Depends(get_db)):
    query = BASE_QUERY + """
        WHERE DATE(Fecha) BETWEEN :inicio AND :fin;
    """
    return await fetch_aggregated_data(db, query, {"inicio": inicio, "fin": fin})


@reportes.get("/bimestre")
async def ventas_bimestre(bimestre: int, anio: int, db: AsyncSession = Depends(get_db)):
    if bimestre < 1 or bimestre > 6:
        raise HTTPException(400, "Bimestre inválido")

    inicio_mes = (bimestre - 1) * 2 + 1
    fin_mes = inicio_mes + 1

    query = BASE_QUERY + """
        WHERE YEAR(Fecha) = :anio
        AND MONTH(Fecha) BETWEEN :inicio AND :fin;
    """

    return await fetch_aggregated_data(
        db, query,
        {"anio": anio, "inicio": inicio_mes, "fin": fin_mes}
    )


@reportes.get("/detalle")
async def reporte_detallado(
        inicio: date = None,
        fin: date = None,
        db: AsyncSession = Depends(get_db)
):
    """
    Retorna un análisis más completo con desglose de costos y márgenes
    """
    where_clause = ""
    params = {}

    if inicio and fin:
        where_clause = "WHERE DATE(Fecha) BETWEEN :inicio AND :fin"
        params = {"inicio": inicio, "fin": fin}

    query = f"""
        SELECT 
            COUNT(DISTINCT id_pedido) as total_pedidos,
            COALESCE(SUM(total_platillos), 0) as total_platillos,
            COALESCE(SUM(platillos_completados), 0) as platillos_completados,
            COALESCE(SUM(platillos_cancelados), 0) as platillos_cancelados,
            COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
                THEN total_ingresos_platillos ELSE 0 END), 0) as ingresos_totales,
            COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
                THEN total_egresos_platillos ELSE 0 END), 0) as egresos_totales,
            COALESCE(SUM(CASE WHEN Estado != 'Cancelado' 
                THEN ganancia_bruta ELSE 0 END), 0) as ganancia_total,
            COALESCE(SUM(egresos_cancelados), 0) as perdidas_cancelaciones,
            ROUND(AVG(CASE WHEN Estado != 'Cancelado' 
                THEN margen_ganancia_porcentaje ELSE NULL END), 2) as margen_promedio,
            COUNT(CASE WHEN Estado = 'Cancelado' THEN 1 END) as pedidos_cancelados,
            COUNT(CASE WHEN Estado IN ('Entregado', 'Pagada') THEN 1 END) as pedidos_completados
        FROM view_reporte_ventas_detallado
        {where_clause};
    """

    return await fetch_aggregated_data(db, query, params)


@reportes.get("/pedidos")
async def obtener_pedidos(
        periodo: str = "hoy",
        page: int = 1,
        limit: int = 50,
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los pedidos con paginación según el periodo seleccionado
    """
    offset = (page - 1) * limit

    # Filtro según el periodo
    where_clause = ""
    if periodo == "hoy":
        where_clause = "WHERE DATE(p.Fecha) = CURDATE()"
    elif periodo == "semana":
        where_clause = "WHERE YEARWEEK(p.Fecha, 1) = YEARWEEK(CURDATE(), 1)"
    elif periodo == "mes":
        where_clause = "WHERE YEAR(p.Fecha) = YEAR(CURDATE()) AND MONTH(p.Fecha) = MONTH(CURDATE())"

    # Consulta principal con paginación
    query = f"""
        SELECT 
            p.id_pedido,
            p.Fecha,
            COUNT(dp.id_detalle) as total_platillos,
            p.total,
            p.Estado,
            p.Tipo_pedido
        FROM pedido p
        LEFT JOIN detalle_pedido dp ON p.id_pedido = dp.id_pedido
        {where_clause}
        GROUP BY p.id_pedido, p.Fecha, p.total, p.Estado, p.Tipo_pedido
        ORDER BY p.Fecha DESC
        LIMIT :limit OFFSET :offset;
    """

    # Consulta para contar total
    count_query = f"""
        SELECT COUNT(DISTINCT p.id_pedido) as total
        FROM pedido p
        {where_clause};
    """

    # Ejecutar queries
    result = db.execute(text(query), {"limit": limit, "offset": offset})
    orders = [dict(row) for row in result.mappings().all()]

    count_result = db.execute(text(count_query))
    total = count_result.scalar()

    # Convertir Decimals a float
    for order in orders:
        if isinstance(order.get('total'), Decimal):
            order['total'] = float(order['total'])

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "total_pages": (total + limit - 1) // limit
    }


@reportes.get("/pedidos/intervalo")
async def obtener_pedidos_intervalo(
        inicio: date,
        fin: date,
        page: int = 1,
        limit: int = 50,
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los pedidos con paginación según un intervalo de fechas
    """
    offset = (page - 1) * limit

    # Consulta principal con paginación
    query = """
        SELECT 
            p.id_pedido,
            p.Fecha,
            COUNT(dp.id_detalle) as total_platillos,
            p.total,
            p.Estado,
            p.Tipo_pedido
        FROM pedido p
        LEFT JOIN detalle_pedido dp ON p.id_pedido = dp.id_pedido
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin
        GROUP BY p.id_pedido, p.Fecha, p.total, p.Estado, p.Tipo_pedido
        ORDER BY p.Fecha DESC
        LIMIT :limit OFFSET :offset;
    """

    # Consulta para contar total
    count_query = """
        SELECT COUNT(DISTINCT p.id_pedido) as total
        FROM pedido p
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin;
    """

    # Ejecutar queries
    result = db.execute(text(query), {"inicio": inicio, "fin": fin, "limit": limit, "offset": offset})
    orders = [dict(row) for row in result.mappings().all()]

    count_result = db.execute(text(count_query), {"inicio": inicio, "fin": fin})
    total = count_result.scalar()

    # Convertir Decimals a float
    for order in orders:
        if isinstance(order.get('total'), Decimal):
            order['total'] = float(order['total'])

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "total_pages": (total + limit - 1) // limit
    }


@reportes.get("/graficas/{periodo}")
async def obtener_datos_graficas(
        periodo: str = "hoy",
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene datos para las gráficas según el periodo
    """
    # Filtro según el periodo
    where_clause = ""
    if periodo == "hoy":
        where_clause = "WHERE DATE(p.Fecha) = CURDATE()"
    elif periodo == "semana":
        where_clause = "WHERE YEARWEEK(p.Fecha, 1) = YEARWEEK(CURDATE(), 1)"
    elif periodo == "mes":
        where_clause = "WHERE YEAR(p.Fecha) = YEAR(CURDATE()) AND MONTH(p.Fecha) = MONTH(CURDATE())"

    # 1. VENTAS POR PERÍODO (línea de tiempo)
    if periodo == "hoy":
        # Por hora del día
        query_ventas = f"""
            SELECT 
                HOUR(p.Fecha) as periodo,
                CONCAT(HOUR(p.Fecha), 'h') as name,
                COUNT(DISTINCT p.id_pedido) as pedidos,
                COALESCE(SUM(p.total), 0) as ventas
            FROM pedido p
            {where_clause}
            GROUP BY HOUR(p.Fecha), CONCAT(HOUR(p.Fecha), 'h')
            ORDER BY periodo;
        """
    elif periodo == "semana":
        # Por día de la semana
        query_ventas = f"""
            SELECT 
                DAYOFWEEK(p.Fecha) as periodo,
                CASE DAYOFWEEK(p.Fecha)
                    WHEN 1 THEN 'Domingo'
                    WHEN 2 THEN 'Lunes'
                    WHEN 3 THEN 'Martes'
                    WHEN 4 THEN 'Miércoles'
                    WHEN 5 THEN 'Jueves'
                    WHEN 6 THEN 'Viernes'
                    WHEN 7 THEN 'Sábado'
                END as name,
                COUNT(DISTINCT p.id_pedido) as pedidos,
                COALESCE(SUM(p.total), 0) as ventas
            FROM pedido p
            {where_clause}
            GROUP BY DAYOFWEEK(p.Fecha), 
                    CASE DAYOFWEEK(p.Fecha)
                        WHEN 1 THEN 'Domingo'
                        WHEN 2 THEN 'Lunes'
                        WHEN 3 THEN 'Martes'
                        WHEN 4 THEN 'Miércoles'
                        WHEN 5 THEN 'Jueves'
                        WHEN 6 THEN 'Viernes'
                        WHEN 7 THEN 'Sábado'
                    END
            ORDER BY periodo;
        """
    else:  # mes
        # Por día del mes
        query_ventas = f"""
            SELECT 
                DAY(p.Fecha) as periodo,
                CONCAT('Día ', DAY(p.Fecha)) as name,
                COUNT(DISTINCT p.id_pedido) as pedidos,
                COALESCE(SUM(p.total), 0) as ventas
            FROM pedido p
            {where_clause}
            GROUP BY DAY(p.Fecha), CONCAT('Día ', DAY(p.Fecha))
            ORDER BY periodo;
        """

    result_ventas = db.execute(text(query_ventas))
    ventas_data = []
    for row in result_ventas.mappings().all():
        ventas_data.append({
            "name": row['name'],
            "pedidos": int(row['pedidos']),
            "ventas": float(row['ventas']) if isinstance(row['ventas'], Decimal) else row['ventas']
        })

    # 2. TOP PLATILLOS - Contamos registros en detalle_pedido
    query_platillos = f"""
        SELECT 
            pl.Nombre_platillo as name,
            COUNT(dp.id_detalle) as cantidad,
            COALESCE(SUM(dp.Precio_unitario), 0) as ingresos
        FROM detalle_pedido dp
        INNER JOIN platillo pl ON dp.id_platillo = pl.id_platillo
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        {where_clause}
        AND p.Estado != 'Cancelado'
        AND dp.estado NOT IN ('cancelado')
        GROUP BY pl.id_platillo, pl.Nombre_platillo
        ORDER BY cantidad DESC
        LIMIT 5;
    """

    result_platillos = db.execute(text(query_platillos))
    platillos_data = []
    for row in result_platillos.mappings().all():
        platillos_data.append({
            "name": row['name'],
            "cantidad": int(row['cantidad']) if row['cantidad'] else 0,
            "ingresos": float(row['ingresos']) if isinstance(row['ingresos'], Decimal) else row['ingresos']
        })

    # 3. DISTRIBUCIÓN (preparados vs cancelados)
    query_distribucion = f"""
        SELECT 
            SUM(CASE WHEN dp.estado IN ('listo', 'servido') THEN 1 ELSE 0 END) as preparados,
            SUM(CASE WHEN dp.estado = 'cancelado' THEN 1 ELSE 0 END) as cancelados
        FROM detalle_pedido dp
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        {where_clause};
    """

    result_dist = db.execute(text(query_distribucion))
    dist_row = result_dist.mappings().first()

    distribucion_data = [
        {
            "name": "Preparados",
            "value": int(dist_row['preparados']) if dist_row['preparados'] else 0
        },
        {
            "name": "Cancelados",
            "value": int(dist_row['cancelados']) if dist_row['cancelados'] else 0
        }
    ]

    return {
        "ventas_por_periodo": ventas_data,
        "platillos_top": platillos_data,
        "distribucion": distribucion_data
    }


@reportes.get("/graficas/intervalo")
async def obtener_datos_graficas_intervalo(
        inicio: date,
        fin: date,
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene datos para las gráficas según un intervalo de fechas
    """
    where_clause = "WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin"
    params = {"inicio": inicio, "fin": fin}

    # Por día en el rango
    query_ventas = """
        SELECT 
            DATE(p.Fecha) as periodo,
            DATE_FORMAT(p.Fecha, '%d/%m') as name,
            COUNT(DISTINCT p.id_pedido) as pedidos,
            COALESCE(SUM(p.total), 0) as ventas
        FROM pedido p
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin
        GROUP BY DATE(p.Fecha), DATE_FORMAT(p.Fecha, '%d/%m')
        ORDER BY periodo;
    """

    result_ventas = db.execute(text(query_ventas), params)
    ventas_data = []
    for row in result_ventas.mappings().all():
        ventas_data.append({
            "name": row['name'],
            "pedidos": int(row['pedidos']),
            "ventas": float(row['ventas']) if isinstance(row['ventas'], Decimal) else row['ventas']
        })

    # TOP PLATILLOS
    query_platillos = """
        SELECT 
            pl.Nombre_platillo as name,
            COUNT(dp.id_detalle) as cantidad,
            COALESCE(SUM(dp.Precio_unitario), 0) as ingresos
        FROM detalle_pedido dp
        INNER JOIN platillo pl ON dp.id_platillo = pl.id_platillo
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin
        AND p.Estado != 'Cancelado'
        AND dp.estado NOT IN ('cancelado')
        GROUP BY pl.id_platillo, pl.Nombre_platillo
        ORDER BY cantidad DESC
        LIMIT 5;
    """

    result_platillos = db.execute(text(query_platillos), params)
    platillos_data = []
    for row in result_platillos.mappings().all():
        platillos_data.append({
            "name": row['name'],
            "cantidad": int(row['cantidad']) if row['cantidad'] else 0,
            "ingresos": float(row['ingresos']) if isinstance(row['ingresos'], Decimal) else row['ingresos']
        })

    # DISTRIBUCIÓN
    query_distribucion = """
        SELECT 
            SUM(CASE WHEN dp.estado IN ('listo', 'servido') THEN 1 ELSE 0 END) as preparados,
            SUM(CASE WHEN dp.estado = 'cancelado' THEN 1 ELSE 0 END) as cancelados
        FROM detalle_pedido dp
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin;
    """

    result_dist = db.execute(text(query_distribucion), params)
    dist_row = result_dist.mappings().first()

    distribucion_data = [
        {
            "name": "Preparados",
            "value": int(dist_row['preparados']) if dist_row['preparados'] else 0
        },
        {
            "name": "Cancelados",
            "value": int(dist_row['cancelados']) if dist_row['cancelados'] else 0
        }
    ]

    return {
        "ventas_por_periodo": ventas_data,
        "platillos_top": platillos_data,
        "distribucion": distribucion_data
    }


@reportes.get("/platillo-mas-rentable/{periodo}")
async def obtener_platillo_mas_rentable(
        periodo: str = "hoy",
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el platillo más rentable del periodo
    """
    where_clause = ""
    if periodo == "hoy":
        where_clause = "WHERE DATE(p.Fecha) = CURDATE()"
    elif periodo == "semana":
        where_clause = "WHERE YEARWEEK(p.Fecha, 1) = YEARWEEK(CURDATE(), 1)"
    elif periodo == "mes":
        where_clause = "WHERE YEAR(p.Fecha) = YEAR(CURDATE()) AND MONTH(p.Fecha) = MONTH(CURDATE())"

    query = f"""
        SELECT 
            pl.Nombre_platillo as nombre,
            pl.precio_venta,
            pl.precio_produccion,
            COUNT(dp.id_detalle) as cantidad_vendida,
            COALESCE(SUM(dp.Precio_unitario), 0) as ingresos_totales,
            COALESCE(SUM(pl.precio_produccion), 0) as costos_totales,
            COALESCE(SUM(dp.Precio_unitario - pl.precio_produccion), 0) as ganancia_total,
            ROUND(
                ((pl.precio_venta - pl.precio_produccion) / pl.precio_venta) * 100,
                2
            ) as margen_porcentaje
        FROM detalle_pedido dp
        INNER JOIN platillo pl ON dp.id_platillo = pl.id_platillo
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        {where_clause}
        AND p.Estado != 'Cancelado'
        AND dp.estado NOT IN ('cancelado')
        GROUP BY pl.id_platillo, pl.Nombre_platillo, pl.precio_venta, pl.precio_produccion
        ORDER BY ganancia_total DESC
        LIMIT 1;
    """

    result = db.execute(text(query))
    row = result.mappings().first()

    if not row:
        return {
            "nombre": "N/A",
            "cantidad_vendida": 0,
            "ingresos_totales": 0.0,
            "ganancia_total": 0.0,
            "margen_porcentaje": 0.0
        }

    return {
        "nombre": row['nombre'],
        "cantidad_vendida": int(row['cantidad_vendida']),
        "ingresos_totales": float(row['ingresos_totales']) if isinstance(row['ingresos_totales'], Decimal) else row[
            'ingresos_totales'],
        "ganancia_total": float(row['ganancia_total']) if isinstance(row['ganancia_total'], Decimal) else row[
            'ganancia_total'],
        "margen_porcentaje": float(row['margen_porcentaje']) if isinstance(row['margen_porcentaje'], Decimal) else row[
            'margen_porcentaje']
    }


@reportes.get("/platillo-mas-rentable/intervalo")
async def obtener_platillo_mas_rentable_intervalo(
        inicio: date,
        fin: date,
        db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el platillo más rentable del intervalo de fechas
    """
    query = """
        SELECT 
            pl.Nombre_platillo as nombre,
            pl.precio_venta,
            pl.precio_produccion,
            COUNT(dp.id_detalle) as cantidad_vendida,
            COALESCE(SUM(dp.Precio_unitario), 0) as ingresos_totales,
            COALESCE(SUM(pl.precio_produccion), 0) as costos_totales,
            COALESCE(SUM(dp.Precio_unitario - pl.precio_produccion), 0) as ganancia_total,
            ROUND(
                ((pl.precio_venta - pl.precio_produccion) / pl.precio_venta) * 100,
                2
            ) as margen_porcentaje
        FROM detalle_pedido dp
        INNER JOIN platillo pl ON dp.id_platillo = pl.id_platillo
        INNER JOIN pedido p ON dp.id_pedido = p.id_pedido
        WHERE DATE(p.Fecha) BETWEEN :inicio AND :fin
        AND p.Estado != 'Cancelado'
        AND dp.estado NOT IN ('cancelado')
        GROUP BY pl.id_platillo, pl.Nombre_platillo, pl.precio_venta, pl.precio_produccion
        ORDER BY ganancia_total DESC
        LIMIT 1;
    """

    result = db.execute(text(query), {"inicio": inicio, "fin": fin})
    row = result.mappings().first()

    if not row:
        return {
            "nombre": "N/A",
            "cantidad_vendida": 0,
            "ingresos_totales": 0.0,
            "ganancia_total": 0.0,
            "margen_porcentaje": 0.0
        }

    return {
        "nombre": row['nombre'],
        "cantidad_vendida": int(row['cantidad_vendida']),
        "ingresos_totales": float(row['ingresos_totales']) if isinstance(row['ingresos_totales'], Decimal) else row[
            'ingresos_totales'],
        "ganancia_total": float(row['ganancia_total']) if isinstance(row['ganancia_total'], Decimal) else row[
            'ganancia_total'],
        "margen_porcentaje": float(row['margen_porcentaje']) if isinstance(row['margen_porcentaje'], Decimal) else row[
            'margen_porcentaje']
    }