# tests/conftest.py
import pytest
from unittest.mock import MagicMock, AsyncMock
import os
import sys

# Mock les settings avant l'import
mock_settings = MagicMock()
mock_settings.PROJECT_NAME = "stellarstudio_test"
mock_settings.DATABASE_USER = "test_user"
mock_settings.DATABASE_PASSWORD = "test_password"
mock_settings.DATABASE_HOST = "localhost"
mock_settings.DATABASE_PORT = 3306
mock_settings.DATABASE_NAME = "stellarstudio_test"
mock_settings.DATABASE_URL = "sqlite:///./test.db"
mock_settings.EXPORTER_PASSWORD = "test_password"
mock_settings.REDIS_URL = "redis://localhost:6379"
mock_settings.REDIS_SESSION_DB = 1
mock_settings.CELERY_BROKER_URL = "redis://localhost:6379/0"
mock_settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
mock_settings.CELERY_WORKER_NAME = "test_worker"
mock_settings.HOSTNAME = "localhost"
mock_settings.SESSION_DURATION_MINUTES = 60
mock_settings.SESSION_COOKIE_NAME = "stellarstudio_session"
mock_settings.SESSION_COOKIE_SECURE = False
mock_settings.SESSION_COOKIE_HTTPONLY = True
mock_settings.SESSION_COOKIE_SAMESITE = "lax"
mock_settings.SECRET_KEY = "test_secret_key"
mock_settings.ALGORITHM = "HS256"
mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
mock_settings.MINIO_URL = "localhost:9000"
mock_settings.MINIO_ACCESS_KEY = "test_access_key"
mock_settings.MINIO_SECRET_KEY = "test_secret_key"
mock_settings.MINIO_BUCKET_NAME = "test-bucket"
mock_settings.GRAFANA_ADMIN_PASSWORD = "test_admin"
mock_settings.ADMIN_PASSWORD = "test_admin"

# Patch le module avant son import
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.config'].settings = mock_settings

# Fonction utilitaire pour les mocks SQLAlchemy
def configure_async_mock(mock_session, return_value, method='scalar_one_or_none'):
    """Configure un mock asynchrone pour les tests SQLAlchemy.
    
    Args:
        mock_session: Le mock de session SQLAlchemy
        return_value: La valeur à retourner
        method: La méthode à mocker ('scalar_one_or_none', 'all', etc.)
    
    Examples:
        >>> configure_async_mock(db_session, my_object)  # Pour scalar_one_or_none
        >>> configure_async_mock(db_session, [obj1, obj2], method='all')  # Pour une liste
    """
    mock_session.execute = AsyncMock()
    mock_session.execute.return_value = AsyncMock()
    setattr(mock_session.execute.return_value, method, AsyncMock(return_value=return_value))

# Fixtures existantes
@pytest.fixture
def db_session():
    from .mocks.db import create_db_session_mock
    return create_db_session_mock()

@pytest.fixture
def redis_client():
    from .mocks.redis import RedisMock
    return RedisMock()

@pytest.fixture
def minio_client():
    from .mocks.minio import MinioClientMock
    return MinioClientMock()

# Nouvelle fixture pour les mocks SQLAlchemy
@pytest.fixture
def configure_db_mock():
    """Fixture qui retourne la fonction de configuration de mock SQLAlchemy.
    
    Returns:
        callable: Fonction pour configurer facilement les mocks de base de données
    
    Examples:
        >>> async def test_my_function(db_session, configure_db_mock):
        >>>     configure_db_mock(db_session, my_return_value)
        >>>     result = await my_function()
        >>>     assert result == expected
    """
    return configure_async_mock