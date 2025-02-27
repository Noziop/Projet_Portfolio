from redis.asyncio import Redis
from app.core.config import settings

# Client Redis asynchrone
redis_client = Redis(
    host=settings.REDIS_HOST,  
    port=settings.REDIS_PORT,
    db=settings.REDIS_SESSION_DB
)
