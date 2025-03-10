# app/tasks/common/notifications.py
import logging
from typing import Dict, Any, Union
from uuid import UUID

from app.core.ws.manager import ConnectionManager

# Configuration du logging
notif_logger = logging.getLogger('app.task.common.notifications')

# Singleton pour le WebSocket manager
ws_manager = ConnectionManager()

def send_notification_sync(user_id: Union[str, UUID], message_data: Dict[str, Any]):
    """Envoie une notification WebSocket de manière synchrone"""
    try:
        # Version synchrone pour Celery
        ws_manager.send_message_sync(user_id=user_id, message=message_data)
        notif_logger.info(f"Notification envoyée à l'utilisateur {user_id}")
        return True
    except Exception as e:
        notif_logger.error(f"Erreur lors de l'envoi de la notification: {str(e)}")
        return False

def send_progress_sync(user_id, task_id, progress, message, type="progress"):
    """Envoie une notification de progression synchrone"""
    data = {
        "task_id": str(task_id),
        "progress": progress,
        "message": message,
        "type": type
    }
    return send_notification_sync(user_id, data)

def send_error_sync(user_id, error):
    """Envoie une notification d'erreur synchrone"""
    data = {
        "error": error,
        "type": "error"
    }
    return send_notification_sync(user_id, data)
