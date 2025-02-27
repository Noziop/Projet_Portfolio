# app/services/auth/session.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import json
from redis.asyncio import Redis
from prometheus_client import Counter, Histogram
from app.core.config import settings

# Métriques Prometheus
session_operations = Counter(
    'session_operations_total',
    'Total number of session operations',
    ['operation']  # create, get, update, delete
)

session_duration = Histogram(
    'session_duration_seconds',
    'Time spent processing session operations',
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0)
)

class SessionService:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "session:"
        self.expiration = timedelta(minutes=settings.SESSION_DURATION_MINUTES)

    async def create_session(self, user_id: UUID, data: Dict[str, Any]) -> str:
        """Crée une nouvelle session pour un utilisateur"""
        with session_duration.time():
            session_id = str(uuid4())
            session_key = f"{self.prefix}{session_id}"
            
            session_data = {
                "user_id": str(user_id),
                "created_at": datetime.utcnow().isoformat(),
                **data
            }
            
            await self.redis.set(
                session_key,
                json.dumps(session_data),
                ex=int(self.expiration.total_seconds())
            )
            
            session_operations.labels(operation='create').inc()
            return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une session"""
        with session_duration.time():
            session_key = f"{self.prefix}{session_id}"
            data = await self.redis.get(session_key)
            
            if data:
                # Rafraîchit l'expiration de la session
                await self.redis.expire(
                    session_key,
                    int(self.expiration.total_seconds())
                )
                session_operations.labels(operation='get').inc()
                return json.loads(data)
            return None

    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Met à jour les données d'une session existante"""
        with session_duration.time():
            session_key = f"{self.prefix}{session_id}"
            existing_data = await self.redis.get(session_key)
            
            if existing_data:
                updated_data = {**json.loads(existing_data), **data}
                await self.redis.set(
                    session_key,
                    json.dumps(updated_data),
                    ex=int(self.expiration.total_seconds())
                )
                session_operations.labels(operation='update').inc()
                return True
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Supprime une session"""
        with session_duration.time():
            session_key = f"{self.prefix}{session_id}"
            result = await self.redis.delete(session_key) > 0
            if result:
                session_operations.labels(operation='delete').inc()
            return result

    async def get_user_sessions(self, user_id: UUID) -> list[str]:
        """Récupère toutes les sessions actives d'un utilisateur"""
        all_sessions = []
        async for key in self.redis.scan_iter(f"{self.prefix}*"):
            data = await self.redis.get(key)
            if data:
                session_data = json.loads(data)
                if session_data.get("user_id") == str(user_id):
                    all_sessions.append(key.decode().replace(self.prefix, ""))
        return all_sessions

    async def clear_user_sessions(self, user_id: UUID) -> int:
        """Supprime toutes les sessions d'un utilisateur"""
        sessions = await self.get_user_sessions(user_id)
        count = 0
        for session_id in sessions:
            if await self.delete_session(session_id):
                count += 1
        return count
