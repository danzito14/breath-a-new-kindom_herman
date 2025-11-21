import uuid
import json
import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import Session
import google.generativeai as genai

from src.core.db_credentials import get_db
from src.db.model.pedidos.repartidores_model import repartidores, lista_repartidores
from src.db.model.pedidos.pedidos_model import pedido, detalle_pedido
from src.db.model.direcciones_usuario_model import direcciones_usuario
from src.db.model.usuario_model import usuarios
from src.core.websocket_manager import manager

logger = logging.getLogger(__name__)

# Configurar Gemini
GEMINI_API_KEY = "AIzaSyDSysCn84VSLyxi0M2trjdnAcffdNzs13I"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("⚠️ GEMINI_API_KEY no configurada. La asignación con IA no funcionará.")


class RepartidorService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    def obtener_repartidores_disponibles(self) -> List[Dict[str, Any]]:
        """Obtiene todos los repartidores activos"""
        query = (
            select(
                repartidores.c.id_repartidor,
                repartidores.c.id_usuario,
                repartidores.c.activo,
                repartidores.c.en_ruta,
                repartidores.c.pedidos_asignados,
                repartidores.c.estado,
                repartidores.c.id_pedido,
                func.concat(usuarios.c.Nombre, " ", usuarios.c.Apellido).label("nombre_completo"),
                usuarios.c.Num_telefonico
            )
            .join(usuarios, usuarios.c.id_usuario == repartidores.c.id_usuario)
            .where(repartidores.c.activo == True)
        )

        rows = self.db.execute(query).all()

        return [
            {
                "id_repartidor": r.id_repartidor,
                "id_usuario": r.id_usuario,
                "nombre_completo": r.nombre_completo,
                "telefono": r.Num_telefonico,
                "activo": r.activo,
                "en_ruta": r.en_ruta,
                "pedidos_asignados": r.pedidos_asignados,
                "estado": r.estado,
                "pedidos_actuales": self._obtener_pedidos_repartidor(r.id_usuario),
                "id_pedido": r.id_pedido
            }
            for r in rows
        ]

    def _obtener_pedidos_repartidor(self, id_usuario: str) -> List[Dict[str, Any]]:
        """Obtiene los pedidos asignados a un repartidor específico desde lista_repartidores"""
        query = (
            select(
                pedido.c.id_pedido,
                pedido.c.Estado,
                pedido.c.total,
                direcciones_usuario.c.Calle,
                direcciones_usuario.c.No_ext,
                direcciones_usuario.c.Colonia,
                direcciones_usuario.c.Ciudad,
                direcciones_usuario.c.Municipio,
                direcciones_usuario.c.instrucciones_add,
                direcciones_usuario.c.temporal,
                lista_repartidores.c.estado_pedido,
                func.concat(usuarios.c.Nombre, " ", usuarios.c.Apellido).label("cliente")
            )
            .join(lista_repartidores, lista_repartidores.c.id_pedido == pedido.c.id_pedido)
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .join(usuarios, usuarios.c.id_usuario == pedido.c.id_usuario)
            .where(
                and_(
                    lista_repartidores.c.id_usuario == id_usuario,
                    lista_repartidores.c.estado_pedido.in_(["pendiente", "en_camino"])
                )
            )
        )

        rows = self.db.execute(query).all()

        return [
            {
                "id_pedido": r.id_pedido,
                "estado": r.Estado,
                "estado_lista": r.estado_pedido,
                "total": r.total,
                "cliente": r.cliente,
                "direccion": r.instrucciones_add if r.temporal else f"{r.Calle} {r.No_ext}, {r.Colonia}, {r.Ciudad}",
                "ciudad": r.Ciudad,
                "municipio": r.Municipio
            }
            for r in rows
        ]

    def _construir_prompt_gemini(
            self,
            pedido_nuevo: Dict[str, Any],
            repartidores: List[Dict[str, Any]]
    ) -> str:
        """Construye el prompt para Gemini con toda la información necesaria"""

        prompt = f"""Eres un asistente de optimización de rutas para un restaurante en Los Mochis, Sinaloa, México.
Tu tarea es asignar un nuevo pedido al repartidor más adecuado.

PEDIDO NUEVO:
- ID: {pedido_nuevo['id_pedido']}
- Dirección de entrega: {pedido_nuevo['direccion']}
- Ciudad: {pedido_nuevo['ciudad']}
- Municipio: {pedido_nuevo['municipio']}
- Cliente: {pedido_nuevo['cliente']}
- Total: ${pedido_nuevo['total']} MXN

REPARTIDORES DISPONIBLES:
"""

        for idx, rep in enumerate(repartidores, 1):
            prompt += f"""
Repartidor {idx}:
- ID: {rep['id_repartidor']}
- ID Usuario: {rep['id_usuario']}
- Nombre: {rep['nombre_completo']}
- Estado: {rep['estado']}
- Pedidos asignados actualmente: {rep['pedidos_asignados']}
"""
            if rep['pedidos_actuales']:
                prompt += "- Pedidos actuales:\n"
                for p in rep['pedidos_actuales']:
                    prompt += f"  * {p['ciudad']}, {p['municipio']} - {p['direccion']}\n"
            else:
                prompt += "- Sin pedidos asignados (disponible inmediatamente)\n"

        prompt += """

CRITERIOS DE ASIGNACIÓN (en orden de prioridad):
1. **Proximidad geográfica**: Prioriza repartidores que ya tienen pedidos hacia la misma ciudad/municipio
2. **Carga de trabajo**: Balancea entre repartidores
3. **Disponibilidad**: Si un repartidor está "En local" sin pedidos, tiene máxima prioridad
4. **Eficiencia de ruta**: Agrupa pedidos que estén cerca geográficamente

REGLAS IMPORTANTES:
- Si el pedido es para Los Mochis y un repartidor ya va hacia allá, asígnalo a él
- Si el pedido es para Guasave/otra ciudad, asigna a un repartidor diferente
- Considera que Los Mochis es la base del restaurante

RESPONDE ÚNICAMENTE EN FORMATO JSON con esta estructura:
{{
    "id_repartidor_seleccionado": "uuid-del-repartidor",
    "id_usuario_seleccionado": "uuid-del-usuario-repartidor",
    "razon": "Explicación breve de por qué elegiste este repartidor (máximo 100 caracteres)",
    "prioridad": "alta/media/baja",
    "eficiencia_estimada": "buena/excelente/regular"
}}

NO incluyas ningún texto adicional fuera del JSON."""

        return prompt

    async def asignar_pedido_con_ia(self, id_pedido: str) -> Dict[str, Any]:
        """Usa Gemini para asignar inteligentemente un pedido a un repartidor"""
        try:
            # 1. Obtener información del pedido
            pedido_info = self._obtener_info_pedido(id_pedido)
            if not pedido_info:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            # 2. Obtener repartidores disponibles
            repartidores_disponibles = self.obtener_repartidores_disponibles()

            if not repartidores_disponibles:
                raise HTTPException(status_code=400, detail="No hay repartidores disponibles")

            # 3. Si Gemini no está configurado, usar fallback
            if not self.model:
                logger.warning("Gemini no configurado, usando asignación por defecto")
                return await self._asignar_pedido_fallback(id_pedido, pedido_info, repartidores_disponibles)

            # 4. Construir prompt para Gemini
            prompt = self._construir_prompt_gemini(pedido_info, repartidores_disponibles)

            # 5. Llamar a Gemini
            response = self.model.generate_content(prompt)
            respuesta_texto = response.text.strip()

            # Limpiar la respuesta si viene con markdown
            if respuesta_texto.startswith("```json"):
                respuesta_texto = respuesta_texto.replace("```json", "").replace("```", "").strip()
            elif respuesta_texto.startswith("```"):
                respuesta_texto = respuesta_texto.replace("```", "").strip()

            decision = json.loads(respuesta_texto)

            id_repartidor_seleccionado = decision["id_repartidor_seleccionado"]
            id_usuario_seleccionado = decision["id_usuario_seleccionado"]
            razon = decision.get("razon", "Asignación automática")

            # 6. Asignar el pedido al repartidor (actualiza pedidos y repartidores)
            resultado = self._asignar_pedido_a_repartidor(id_pedido, id_repartidor_seleccionado)

            if not resultado:
                raise HTTPException(status_code=500, detail="Error al asignar pedido en BD")

            # 7. Registrar en lista_repartidores
            self._registrar_en_lista_repartidores(id_pedido, id_usuario_seleccionado)

            # 8. Notificar al repartidor vía WebSocket
            await self._notificar_nuevo_pedido_repartidor(
                id_repartidor_seleccionado,
                id_pedido,
                pedido_info
            )

            # 9. Notificar a admin sobre la asignación
            await self._notificar_asignacion_admin(id_pedido, id_repartidor_seleccionado, razon)

            logger.info(f"✅ Pedido {id_pedido} asignado a {id_repartidor_seleccionado}: {razon}")

            return {
                "success": True,
                "id_pedido": id_pedido,
                "id_repartidor": id_repartidor_seleccionado,
                "id_usuario": id_usuario_seleccionado,
                "razon_asignacion": razon,
                "prioridad": decision.get("prioridad", "media"),
                "eficiencia": decision.get("eficiencia_estimada", "buena"),
                "detalles_pedido": pedido_info
            }

        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear respuesta de Gemini: {e}")
            logger.error(f"Respuesta recibida: {respuesta_texto}")
            # Fallback: asignar al repartidor con menos pedidos
            return await self._asignar_pedido_fallback(id_pedido, pedido_info, repartidores_disponibles)

        except Exception as e:
            logger.error(f"Error en asignación con IA: {e}")
            # Intentar fallback antes de fallar completamente
            try:
                return await self._asignar_pedido_fallback(id_pedido, pedido_info, repartidores_disponibles)
            except:
                raise HTTPException(status_code=500, detail=f"Error al asignar pedido: {str(e)}")

    def _obtener_info_pedido(self, id_pedido: str) -> Optional[Dict[str, Any]]:
        """Obtiene información completa del pedido"""
        query = (
            select(
                pedido.c.id_pedido,
                pedido.c.total,
                pedido.c.Estado,
                direcciones_usuario.c.Calle,
                direcciones_usuario.c.No_ext,
                direcciones_usuario.c.Colonia,
                direcciones_usuario.c.Ciudad,
                direcciones_usuario.c.Municipio,
                direcciones_usuario.c.Estado.label("estado_direccion"),
                direcciones_usuario.c.CP,
                direcciones_usuario.c.instrucciones_add,
                direcciones_usuario.c.temporal,
                func.concat(usuarios.c.Nombre, " ", usuarios.c.Apellido).label("nombre_cliente"),
                usuarios.c.Num_telefonico
            )
            .join(direcciones_usuario, direcciones_usuario.c.id_direccion == pedido.c.id_direccion)
            .join(usuarios, usuarios.c.id_usuario == pedido.c.id_usuario)
            .where(pedido.c.id_pedido == id_pedido)
        )

        result = self.db.execute(query).first()

        if not result:
            return None

        direccion_completa = (
            result.instrucciones_add if result.temporal
            else f"{result.Calle} {result.No_ext}, {result.Colonia}, {result.Ciudad}, {result.estado_direccion}, CP {result.CP}"
        )

        return {
            "id_pedido": result.id_pedido,
            "total": float(result.total) if result.total else 0,
            "estado": result.Estado,
            "direccion": direccion_completa,
            "ciudad": result.Ciudad,
            "municipio": result.Municipio,
            "cliente": result.nombre_cliente,
            "telefono": result.Num_telefonico,
            "instrucciones": result.instrucciones_add
        }

    def _asignar_pedido_a_repartidor(self, id_pedido: str, id_repartidor: str) -> bool:
        """Asigna físicamente el pedido al repartidor en la base de datos"""
        try:
            # Actualizar el pedido
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(
                    id_repartidor=id_repartidor,
                    Estado="En camino"
                )
            )

            # Actualizar contador de pedidos del repartidor
            self.db.execute(
                update(repartidores)
                .where(repartidores.c.id_repartidor == id_repartidor)
                .values(
                    pedidos_asignados=repartidores.c.pedidos_asignados + 1,
                    en_ruta=True,
                    estado="Repartiendo"
                )
            )

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al asignar pedido: {e}")
            return False

    def _registrar_en_lista_repartidores(self, id_pedido: str, id_usuario: str):
        """Registra la asignación en la tabla lista_repartidores"""
        try:
            nueva_asignacion = {
                "id_lista_r": str(uuid.uuid4()),
                "id_pedido": id_pedido,
                "id_usuario": id_usuario,
                "estado_pedido": "en_camino",
                "fecha_asignado": datetime.now()
            }

            self.db.execute(lista_repartidores.insert().values(nueva_asignacion))
            self.db.commit()

            logger.info(f"✅ Pedido {id_pedido} registrado en lista_repartidores para usuario {id_usuario}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al registrar en lista_repartidores: {e}")
            raise

    async def _asignar_pedido_fallback(
            self,
            id_pedido: str,
            pedido_info: Dict[str, Any],
            repartidores_disponibles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Asignación de respaldo si falla Gemini"""
        # Elegir el repartidor con menos pedidos
        repartidor_seleccionado = min(
            repartidores_disponibles,
            key=lambda r: r['pedidos_asignados']
        )

        self._asignar_pedido_a_repartidor(id_pedido, repartidor_seleccionado['id_repartidor'])

        # Registrar en lista_repartidores
        self._registrar_en_lista_repartidores(id_pedido, repartidor_seleccionado['id_usuario'])

        await self._notificar_nuevo_pedido_repartidor(
            repartidor_seleccionado['id_repartidor'],
            id_pedido,
            pedido_info
        )

        await self._notificar_asignacion_admin(
            id_pedido,
            repartidor_seleccionado['id_repartidor'],
            "Asignación automática (sin IA)"
        )

        logger.info(f"✅ Pedido {id_pedido} asignado por fallback a {repartidor_seleccionado['nombre_completo']}")

        return {
            "success": True,
            "id_pedido": id_pedido,
            "id_repartidor": repartidor_seleccionado['id_repartidor'],
            "id_usuario": repartidor_seleccionado['id_usuario'],
            "razon_asignacion": "Asignación automática: repartidor con menos carga",
            "prioridad": "media",
            "eficiencia": "buena",
            "detalles_pedido": pedido_info
        }

    async def _notificar_nuevo_pedido_repartidor(
            self,
            id_repartidor: str,
            id_pedido: str,
            pedido_info: Dict[str, Any]
    ):
        """Notifica al repartidor sobre el nuevo pedido asignado"""
        try:
            mensaje = {
                "tipo": "nuevo_pedido_asignado",
                "id_repartidor": id_repartidor,
                "id_pedido": id_pedido,
                "detalles": pedido_info,
                "timestamp": datetime.now().isoformat()
            }

            # Enviar a grupo de repartidores
            await manager.broadcast_to_group(mensaje, "repartidor")

            logger.info(f"📡 Notificación enviada a repartidor {id_repartidor}")

        except Exception as e:
            logger.error(f"❌ Error al notificar repartidor: {e}")

    async def _notificar_asignacion_admin(self, id_pedido: str, id_repartidor: str, razon: str):
        """Notifica a administradores sobre la asignación"""
        try:
            mensaje = {
                "tipo": "pedido_asignado_repartidor",
                "id_pedido": id_pedido,
                "id_repartidor": id_repartidor,
                "razon": razon,
                "timestamp": datetime.now().isoformat()
            }

            await manager.broadcast_to_group(mensaje, "admin")
            logger.info(f"📡 Notificación de asignación enviada a admins")

        except Exception as e:
            logger.error(f"❌ Error al notificar admin: {e}")

    def marcar_pedido_entregado(self, id_pedido: str, id_usuario: str) -> Dict[str, Any]:
        """Marca un pedido como entregado y actualiza el estado del repartidor"""
        try:
            # Obtener id_repartidor desde el pedido
            pedido_query = select(
                pedido.c.id_repartidor
            ).where(pedido.c.id_pedido == id_pedido)

            result = self.db.execute(pedido_query).first()

            if not result:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            id_repartidor = result.id_repartidor

            # Actualizar pedido
            self.db.execute(
                update(pedido)
                .where(pedido.c.id_pedido == id_pedido)
                .values(Estado="Entregado")
            )

            # Actualizar lista_repartidores
            self.db.execute(
                update(lista_repartidores)
                .where(
                    and_(
                        lista_repartidores.c.id_pedido == id_pedido,
                        lista_repartidores.c.id_usuario == id_usuario
                    )
                )
                .values(estado_pedido="entregado")
            )

            # Reducir contador del repartidor
            self.db.execute(
                update(repartidores)
                .where(repartidores.c.id_repartidor == id_repartidor)
                .values(
                    pedidos_asignados=repartidores.c.pedidos_asignados - 1
                )
            )

            # Si ya no tiene pedidos, cambiar estado
            repartidor = self.db.execute(
                select(repartidores.c.pedidos_asignados)
                .where(repartidores.c.id_repartidor == id_repartidor)
            ).first()

            if repartidor and repartidor.pedidos_asignados <= 0:
                self.db.execute(
                    update(repartidores)
                    .where(repartidores.c.id_repartidor == id_repartidor)
                    .values(
                        en_ruta=False,
                        estado="En local",
                        pedidos_asignados=0
                    )
                )

            self.db.commit()

            logger.info(f"✅ Pedido {id_pedido} marcado como entregado por usuario {id_usuario}")

            return {
                "success": True,
                "message": "Pedido marcado como entregado",
                "id_pedido": id_pedido
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error al marcar entregado: {e}")
            raise HTTPException(status_code=500, detail=f"Error al marcar entregado: {str(e)}")