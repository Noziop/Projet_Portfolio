# app/core/ws/manager.py
from typing import Dict, Any, Union
from uuid import UUID
from fastapi import WebSocket
from prometheus_client import Counter, Gauge
import logging
import json

# Métriques Prometheus
ws_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections'
)

ws_messages = Counter(
    'websocket_messages_total',
    'Total number of WebSocket messages',
    ['type']  # update, error, preview
)

# Logger pour les méthodes synchrones
ws_logger = logging.getLogger('app.ws.manager')

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, WebSocket] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket):
        """Établit une nouvelle connexion WebSocket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        ws_connections.inc()

    async def disconnect(self, user_id: UUID):
        """Ferme une connexion WebSocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            ws_connections.dec()

    async def send_processing_update(self, user_id: UUID, data: Dict[str, Any]):
        """Envoie une mise à jour de processing"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json({
                "type": "processing_update",
                "data": data
            })
            ws_messages.labels(type='update').inc()

    async def send_preview(self, user_id: UUID, preview_data: Dict[str, Any]):
        """Envoie une preview d'image"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json({
                "type": "preview",
                "data": preview_data
            })
            ws_messages.labels(type='preview').inc()

    async def send_error(self, user_id: UUID, error: str):
        """Envoie une notification d'erreur"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json({
                "type": "error",
                "message": error
            })
            ws_messages.labels(type='error').inc()

    async def broadcast(self, message: Dict[str, Any]):
        """Envoie un message à tous les clients connectés"""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)
            
    # ------ Méthodes synchrones pour Celery ------
    
    def send_message_sync(self, user_id: Union[str, UUID], message: Dict[str, Any]):
        """Version synchrone pour envoyer un message (pour Celery)
        
        Dans un contexte Celery synchrone, nous ne pouvons pas directement
        envoyer des WebSockets. Cette méthode enregistre le message et,
        si configuré, utilise Redis pour communiquer avec le processus asynchrone.
        """
        user_id_str = str(user_id)
        
        # Vérifier si l'utilisateur est connecté
        is_connected = user_id_str in [str(uid) for uid in self.active_connections.keys()]
        
        # Journaliser le message
        ws_logger.info(f"Message pour l'utilisateur {user_id_str}: {json.dumps(message)}")
        
        # Incrémenter le compteur Prometheus
        message_type = message.get('type', 'unknown')
        ws_messages.labels(type=message_type).inc()
        
        # Option: utiliser Redis pour communiquer avec le processus asynchrone
        import redis
        from app.core.config import settings
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.publish(f"ws_notifications:{user_id_str}", json.dumps(message))
        
        return is_connected
    
    def send_processing_update_sync(self, user_id: Union[str, UUID], data: Dict[str, Any]):
        """Version synchrone de send_processing_update"""
        return self.send_message_sync(user_id, {
            "type": "processing_update",
            "data": data
        })
    
    def send_preview_sync(self, user_id: Union[str, UUID], preview_data: Dict[str, Any]):
        """Version synchrone de send_preview"""
        return self.send_message_sync(user_id, {
            "type": "preview",
            "data": preview_data
        })
    
    def send_error_sync(self, user_id: Union[str, UUID], error: str):
        """Version synchrone de send_error"""
        return self.send_message_sync(user_id, {
            "type": "error",
            "message": error
        })
