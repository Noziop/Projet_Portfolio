# app/core/cache.py
import json
import logging
import time
from typing import Any, Dict, Optional, TypeVar, Generic, List, Union
from uuid import UUID
from pydantic import BaseModel
import redis
from redis.exceptions import RedisError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base Redis pour le cache
_redis_client = None

# Type générique pour les modèles Pydantic
T = TypeVar('T')

# Classe personnalisée pour l'encodage JSON (pour gérer les UUID)
class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

# Fonction pour obtenir le client Redis
def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            # Utiliser la base de données 1 pour le cache (0 étant pour les sessions)
            _redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=2,  # DB différente des sessions
                decode_responses=False,  # On veut garder les bytes pour JSON
                socket_timeout=5.0
            )
            # Test de connexion
            _redis_client.ping()
            logger.info(f"Connexion Redis établie sur {settings.REDIS_HOST}:{settings.REDIS_PORT}/2")
        except RedisError as e:
            logger.error(f"Impossible de se connecter à Redis: {str(e)}")
            # Fallback à un dict en mémoire si Redis n'est pas disponible
            _redis_client = None
            return None
    return _redis_client

class RedisCache:
    """Service de cache utilisant Redis"""

    @staticmethod
    def _get_key(prefix: str, key: str) -> str:
        """Génère une clé de cache formatée"""
        return f"cache:{prefix}:{key}"

    @staticmethod
    def set(prefix: str, key: str, data: Any, ttl: int = 300) -> bool:
        """Stocke des données dans le cache Redis avec un TTL en secondes"""
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis non disponible, cache ignoré")
            return False

        full_key = RedisCache._get_key(prefix, key)
        
        try:
            # Création d'un objet cache avec métadonnées
            cache_data = {
                "data": data,
                "timestamp": time.time(),
                "etag": f"W/\"{prefix}-{key}-{int(time.time())}\""
            }
            
            # Sérialisation JSON avec gestion des UUID
            serialized = json.dumps(cache_data, cls=UUIDEncoder)
            
            # Stockage dans Redis avec TTL
            result = redis_client.setex(full_key, ttl, serialized)
            
            if result:
                logger.debug(f"Cache mis à jour: {full_key}")
            else:
                logger.warning(f"Échec de mise en cache: {full_key}")
                
            return result
        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Erreur lors du stockage dans Redis: {str(e)}")
            return False

    @staticmethod
    def get(prefix: str, key: str) -> Optional[Dict[str, Any]]:
        """Récupère des données du cache Redis"""
        redis_client = get_redis_client()
        if not redis_client:
            logger.warning("Redis non disponible, cache ignoré")
            return None

        full_key = RedisCache._get_key(prefix, key)
        
        try:
            # Récupération des données
            data = redis_client.get(full_key)
            if not data:
                logger.debug(f"Cache miss: {full_key}")
                return None
                
            # Désérialisation JSON
            cache_entry = json.loads(data)
            logger.debug(f"Cache hit: {full_key}")
            return cache_entry
            
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Erreur lors de la récupération depuis Redis: {str(e)}")
            return None

    @staticmethod
    def delete(prefix: str, key: str) -> bool:
        """Supprime des données du cache Redis"""
        redis_client = get_redis_client()
        if not redis_client:
            return False

        full_key = RedisCache._get_key(prefix, key)
        
        try:
            result = redis_client.delete(full_key)
            return result > 0
        except RedisError as e:
            logger.error(f"Erreur lors de la suppression du cache: {str(e)}")
            return False

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Supprime toutes les clés correspondant à un motif"""
        redis_client = get_redis_client()
        if not redis_client:
            return 0

        try:
            # Utiliser scan_iter pour éviter de bloquer Redis avec KEYS
            keys = redis_client.scan_iter(match=f"cache:{pattern}*")
            count = 0
            
            # Suppression par lots
            pipeline = redis_client.pipeline()
            for key in keys:
                pipeline.delete(key)
                count += 1
                # Exécution par lots de 100
                if count % 100 == 0:
                    pipeline.execute()
                    pipeline = redis_client.pipeline()
            
            # Exécution finale
            if count % 100 != 0:
                pipeline.execute()
                
            logger.info(f"Cache nettoyé: {count} clés supprimées pour le motif '{pattern}'")
            return count
        except RedisError as e:
            logger.error(f"Erreur lors du nettoyage du cache: {str(e)}")
            return 0

    @staticmethod
    def get_ttl(prefix: str, key: str) -> int:
        """Récupère le TTL restant en secondes pour une clé"""
        redis_client = get_redis_client()
        if not redis_client:
            return -2  # -2 signifie clé inexistante dans Redis

        full_key = RedisCache._get_key(prefix, key)
        
        try:
            return redis_client.ttl(full_key)
        except RedisError as e:
            logger.error(f"Erreur lors de la récupération du TTL: {str(e)}")
            return -2

    @staticmethod
    def extend_ttl(prefix: str, key: str, ttl: int) -> bool:
        """Prolonge le TTL d'une clé existante"""
        redis_client = get_redis_client()
        if not redis_client:
            return False

        full_key = RedisCache._get_key(prefix, key)
        
        try:
            return redis_client.expire(full_key, ttl)
        except RedisError as e:
            logger.error(f"Erreur lors de l'extension du TTL: {str(e)}")
            return False 