import asyncio
import json
import uuid
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class SSEManager:
    def __init__(self):
        self.connections: Dict[str, asyncio.Queue] = {}
        
    async def connect(self) -> tuple[str, asyncio.Queue]:
        """Crear una nueva conexión SSE"""
        connection_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        self.connections[connection_id] = queue
        logger.info(f"Nueva conexión SSE: {connection_id}")
        return connection_id, queue
    
    async def disconnect(self, connection_id: str):
        """Desconectar una conexión SSE"""
        if connection_id in self.connections:
            del self.connections[connection_id]
            logger.info(f"Conexión SSE desconectada: {connection_id}")
    
    async def broadcast(self, message: dict):
        """Enviar mensaje a todas las conexiones activas"""
        if not self.connections:
            return
            
        message_str = json.dumps(message)
        logger.info(f"Broadcasting message to {len(self.connections)} connections: {message['type']}")
        
        # Crear lista de tareas para envío concurrente
        tasks = []
        dead_connections = []
        
        for connection_id, queue in self.connections.items():
            try:
                # No usar await aquí, solo agregar a la cola
                queue.put_nowait(message_str)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for connection {connection_id}")
                dead_connections.append(connection_id)
            except Exception as e:
                logger.error(f"Error sending to connection {connection_id}: {e}")
                dead_connections.append(connection_id)
        
        # Limpiar conexiones muertas
        for connection_id in dead_connections:
            await self.disconnect(connection_id)
    
    async def stream(self):
        """Generador para el stream SSE"""
        connection_id, queue = await self.connect()
        
        try:
            # Enviar mensaje inicial de conexión
            yield f"data: {json.dumps({'type': 'connection', 'data': {'status': 'connected'}})}\n\n"
            
            while True:
                try:
                    # Esperar por mensaje con timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Enviar ping cada 30 segundos para mantener la conexión viva
                    yield f"data: {json.dumps({'type': 'ping', 'data': {}})}\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE stream for {connection_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"SSE stream error for {connection_id}: {e}")
        finally:
            await self.disconnect(connection_id)