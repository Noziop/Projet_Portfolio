from typing import Dict, Any
from uuid import UUID
from fastapi import WebSocket
from prometheus_client import Counter, Gauge

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
