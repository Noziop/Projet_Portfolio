# app/core/session.py
from typing import Optional
import json
from redis.asyncio import Redis
from app.core.config import settings

class SessionManager:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_SESSION_DB
        )
        self.prefix = "session:"
        self.expire_time = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def create_session(self, user_id: str, data: dict) -> bool:
        """Crée une session en utilisant l'ID utilisateur comme clé"""
        session_key = f"{self.prefix}{user_id}"
        
        # Préparer les données de session
        session_data = {
            "user_id": user_id,
            **data
        }
        
        try:
            result = await self.redis.setex(
                session_key,
                self.expire_time,
                json.dumps(session_data)
            )
            
            # Vérification immédiate
            verification = await self.redis.get(session_key)
            
            return True
        except Exception as e:
            print(f"Debug - ERREUR création session: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False

    async def get_session(self, user_id: str) -> Optional[dict]:
        """Récupère une session en utilisant l'ID utilisateur comme clé"""
        session_key = f"{self.prefix}{user_id}"
        
        data = await self.redis.get(session_key)
        
        if data:
            # Rafraîchir l'expiration
            await self.redis.expire(session_key, self.expire_time)
            return json.loads(data)
        return None

    async def revoke_session(self, user_id: str) -> bool:
        """Supprime une session en utilisant l'ID utilisateur comme clé"""
        session_key = f"{self.prefix}{user_id}"
        return bool(await self.redis.delete(session_key))

    async def update_session(self, user_id: str, data: dict) -> bool:
        """Met à jour une session existante"""
        session_key = f"{self.prefix}{user_id}"
        existing_data = await self.redis.get(session_key)
        
        if existing_data:
            updated_data = {**json.loads(existing_data), **data}
            await self.redis.setex(
                session_key,
                self.expire_time,
                json.dumps(updated_data)
            )
            return True
        return False
