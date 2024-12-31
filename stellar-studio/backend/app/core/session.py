# app/core/session.py
from typing import Optional
import json
from redis import Redis
from app.core.config import settings

class SessionManager:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.REDIS_URL,
            db=settings.REDIS_SESSION_DB
        )
        self.prefix = "session:"
        self.expire_time = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def create_session(self, user_id: int, data: dict) -> str:
        session_key = f"{self.prefix}{user_id}"
        self.redis.setex(
            session_key,
            self.expire_time,
            json.dumps(data)
        )
        return session_key

    def get_session(self, user_id: int) -> Optional[dict]:
        session_key = f"{self.prefix}{user_id}"
        data = self.redis.get(session_key)
        return json.loads(data) if data else None

    def revoke_session(self, user_id: int) -> bool:
        session_key = f"{self.prefix}{user_id}"
        return bool(self.redis.delete(session_key))
