"""
Servicio de asignación inteligente de pedidos usando Gemini API
Para FastAPI + Python 3.8
"""

from google import genai
from typing import List, Dict, Optional
import os
import json
from datetime import datetime


class GeminiDeliveryAssigner:
    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Gemini
        Si no se proporciona api_key, se toma de la variable de entorno GEMINI_API_KEY
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"  # Modelo rápido y eficiente

    def asignar_pedido(
            self,
            pedido_nuevo: Dict,
            repartidores_disponibles: List[Dict],
            pedidos_actuales: List[Dict]
    ) -> Dict:
        """
        Usa Gemini para decidir a qué repartidor asignar un pedido nuevo

        Args:
            pedido_nuevo: Dict con info del pedido {id, direccion, ciudad, lat, lng}
            repartidores_disponibles: Lista de repartidores con su info
            pedidos_actuales: Lista de pedidos ya asignados

        Returns:
            Dict con la decisión: {
                "id_repartidor": str,
                "razon": str,
                "confianza": float
            }
        """

        # Construir el prompt para Gemini
        prompt = self._construir_prompt(
            pedido_nuevo,
            repartidores_disponibles,
            pedidos_actuales
        )

        try:
            # Llamar a Gemini con instrucciones de responder en JSON
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            # Extraer y parsear la respuesta
            respuesta_texto = response.text.strip()

            # Limpiar markdown si existe
            if respuesta_texto.startswith("```json"):
                respuesta_texto = respuesta_texto.replace("```json", "").replace("```", "").strip()
            elif respuesta_texto.startswith("```"):
                respuesta_texto = respuesta_texto.replace("```", "").strip()

            # Parsear JSON
            decision = json.loads(respuesta_texto)

            return {
                "success": True,
                "id_repartidor": decision.get("id_repartidor"),
                "razon": decision.get("razon"),
                "confianza": decision.get("confianza", 0.8),
                "distancia_estimada": decision.get("distancia_estimada"),
                "tiempo_estimado": decision.get("tiempo_estimado")
            }

        except json.JSONDecodeError as e:
            # Si falla el parseo, retornar el repartidor con menos carga
            print(f"Error parseando respuesta de Gemini: {e}")
            return self._asignacion_fallback(repartidores_disponibles)

        except Exception as e:
            print(f"Error llamando a Gemini: {e}")
            return self._asignacion_fallback(repartidores_disponibles)

    def _construir_prompt(
            self,
            pedido_nuevo: Dict,
            repartidores: List[Dict],
            pedidos_actuales: List[Dict]
    ) -> str:
        """
        Construye el prompt detallado para Gemini
        """

        # Formatear información de repartidores
        info_repartidores = []
        for rep in repartidores:
            pedidos_asignados = [p for p in pedidos_actuales if p.get("id_repartidor") == rep["id_repartidor"]]

            info_rep = {
                "id": rep["id_repartidor"],
                "nombre": rep.get("nombre", f"Repartidor {rep['id_repartidor'][:8]}"),
                "estado": rep.get("estado"),
                "en_ruta": rep.get("en_ruta"),
                "pedidos_actuales": rep.get("pedidos_asignados", 0),
                "ubicacion_actual": rep.get("ubicacion", "Los Mochis, Sinaloa"),
                "pedidos_detalle": [
                    {
                        "destino": p.get("ciudad", p.get("direccion")),
                        "direccion": p.get("direccion")
                    } for p in pedidos_asignados
                ]
            }
            info_repartidores.append(info_rep)

        prompt = f"""Eres un sistema de optimización de rutas para entregas a domicilio en Sinaloa, México.

**PEDIDO NUEVO A ASIGNAR:**
- ID: {pedido_nuevo.get('id_pedido')}
- Ciudad destino: {pedido_nuevo.get('ciudad', 'No especificada')}
- Dirección: {pedido_nuevo.get('direccion', 'No especificada')}
- Coordenadas: {pedido_nuevo.get('latitud', 'N/A')}, {pedido_nuevo.get('longitud', 'N/A')}

**REPARTIDORES DISPONIBLES:**
{json.dumps(info_repartidores, indent=2, ensure_ascii=False)}

**CRITERIOS DE ASIGNACIÓN (en orden de prioridad):**
1. **Cercanía geográfica**: Prioriza repartidores que ya tengan pedidos hacia la misma ciudad o área cercana
2. **Carga de trabajo**: Considera cuántos pedidos ya tiene cada repartidor
3. **Eficiencia de ruta**: Agrupa pedidos que puedan entregarse en una misma ruta
4. **Estado del repartidor**: Preferir repartidores "En local" sobre los que están "Repartiendo"

**CONTEXTO GEOGRÁFICO:**
- Los Mochis y Guasave son las principales ciudades
- Distancia Los Mochis - Guasave: aproximadamente 50-60 km
- Pedidos en la misma ciudad pueden entregarse más eficientemente juntos

**INSTRUCCIONES:**
1. Analiza la ubicación del pedido nuevo vs los pedidos actuales de cada repartidor
2. Evalúa si agrupar este pedido con los existentes de algún repartidor optimiza la ruta
3. Considera la carga de trabajo para balancear entre repartidores
4. Devuelve tu decisión en formato JSON EXACTO (sin texto adicional):

{{
  "id_repartidor": "id_del_repartidor_seleccionado",
  "razon": "Explicación breve de por qué se seleccionó este repartidor (max 100 palabras)",
  "confianza": 0.95,
  "distancia_estimada": "X km",
  "tiempo_estimado": "X minutos"
}}

Responde SOLO con el JSON, sin texto adicional antes o después."""

        return prompt

    def _asignacion_fallback(self, repartidores: List[Dict]) -> Dict:
        """
        Asignación de respaldo si Gemini falla
        Asigna al repartidor con menos pedidos
        """
        if not repartidores:
            return {
                "success": False,
                "error": "No hay repartidores disponibles"
            }

        # Ordenar por cantidad de pedidos (menor primero)
        repartidor_optimo = min(
            repartidores,
            key=lambda r: r.get("pedidos_asignados", 0)
        )

        return {
            "success": True,
            "id_repartidor": repartidor_optimo["id_repartidor"],
            "razon": "Asignación automática por carga balanceada (sistema de respaldo)",
            "confianza": 0.6,
            "metodo": "fallback"
        }

    def obtener_resumen_distribucion(
            self,
            repartidores: List[Dict],
            pedidos: List[Dict]
    ) -> Dict:
        """
        Genera un resumen de la distribución actual usando Gemini
        """
        prompt = f"""Analiza la siguiente distribución de pedidos entre repartidores:

**REPARTIDORES Y SUS PEDIDOS:**
{json.dumps([
            {
                "id": r["id_repartidor"],
                "pedidos_asignados": r.get("pedidos_asignados", 0),
                "estado": r.get("estado"),
                "en_ruta": r.get("en_ruta")
            } for r in repartidores
        ], indent=2, ensure_ascii=False)}

**PEDIDOS TOTALES:** {len(pedidos)}

Proporciona un breve análisis de eficiencia y sugerencias de optimización.
Responde en formato JSON:

{{
  "eficiencia_general": "Alta/Media/Baja",
  "carga_balanceada": true/false,
  "sugerencias": ["sugerencia 1", "sugerencia 2"],
  "alertas": ["alerta 1 si existe"]
}}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            respuesta_texto = response.text.strip()
            if respuesta_texto.startswith("```json"):
                respuesta_texto = respuesta_texto.replace("```json", "").replace("```", "").strip()

            return json.loads(respuesta_texto)

        except Exception as e:
            return {
                "eficiencia_general": "No disponible",
                "error": str(e)
            }