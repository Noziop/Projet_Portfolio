import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import os

# --- Pre-emptive Mocks for StorageService and other global dependencies ---
class MockSettingsGlobalHealth:
    PROJECT_NAME: str = "Test Stellar Studio Health"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_health_api.db"
    REDIS_SESSION_DB: int = 1
    DATABASE_USER: str = "testuser"
    DATABASE_PASSWORD: str = "testpass"
    DATABASE_HOST: str = "testhost"
    DATABASE_PORT: str = "1234"
    DATABASE_NAME: str = "testdb"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "testsecretkey"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

patcher_minio_global_health = patch('minio.Minio')
patcher_settings_global_health = patch('app.core.config.settings', MockSettingsGlobalHealth())
patcher_os_getenv_for_storage_health = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_health = patcher_minio_global_health.start()
mock_settings_started_health = patcher_settings_global_health.start()
mock_os_getenv_for_storage_started_health = patcher_os_getenv_for_storage_health.start()

_global_minio_client_mock_instance_health = MagicMock()
_global_minio_client_mock_instance_health.bucket_exists.return_value = True
mock_minio_class_started_health.return_value = _global_minio_client_mock_instance_health
mock_os_getenv_for_storage_started_health.return_value = 'fits-files'

from app.main import app
# Imports for patching targets in health endpoint
from app.db.session import SessionLocal
from app.core.celery import celery_app
# storage_service is imported by health endpoint, its client will be the mocked one.

def stop_global_patchers_health_api():
    patcher_minio_global_health.stop()
    patcher_settings_global_health.stop()
    patcher_os_getenv_for_storage_health.stop()

@pytest.fixture(scope="session", autouse=True)
def health_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_health_api)

# --- Test Client Fixture REMOVED ---

class TestHealthEndpoint:

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client: # Create client per test
            with patch('app.api.v1.endpoints.health.SessionLocal') as mock_session_local, \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping') as mock_celery_ping, \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists') as mock_bucket_exists:

                mock_db_session_instance = MagicMock()
                mock_session_local.return_value = mock_db_session_instance
                mock_db_session_instance.__enter__.return_value = mock_db_session_instance

                mock_celery_ping.return_value = True
                mock_bucket_exists.return_value = True

                response = await client.get("/api/v1/health/")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["services"]["database"] == "healthy"
                assert data["services"]["redis"] == "healthy"
                assert data["services"]["minio"] == "healthy"

                mock_session_local.assert_called_once()
                mock_db_session_instance.execute.assert_called_once()
                mock_db_session_instance.close.assert_called_once()
                mock_celery_ping.assert_called_once()
                mock_bucket_exists.assert_called_once_with("fits-files")

    @pytest.mark.asyncio
    async def test_health_check_db_unhealthy(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('app.api.v1.endpoints.health.SessionLocal') as mock_session_local, \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping') as mock_celery_ping, \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists') as mock_bucket_exists:

                mock_db_session_instance = MagicMock()
                mock_session_local.return_value = mock_db_session_instance
                mock_db_session_instance.__enter__.return_value = mock_db_session_instance
                mock_db_session_instance.execute.side_effect = Exception("DB Connection Error")

                mock_celery_ping.return_value = True
                mock_bucket_exists.return_value = True

                response = await client.get("/api/v1/health/")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert "unhealthy: DB Connection Error" in data["services"]["database"]
                assert data["services"]["redis"] == "healthy"
                assert data["services"]["minio"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_redis_unhealthy(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('app.api.v1.endpoints.health.SessionLocal') as mock_session_local, \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping') as mock_celery_ping, \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists') as mock_bucket_exists:

                mock_db_session_instance = MagicMock()
                mock_session_local.return_value = mock_db_session_instance
                mock_db_session_instance.__enter__.return_value = mock_db_session_instance

                mock_celery_ping.side_effect = Exception("Redis Connection Error")
                mock_bucket_exists.return_value = True

                response = await client.get("/api/v1/health/")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert data["services"]["database"] == "healthy"
                assert "unhealthy: Redis Connection Error" in data["services"]["redis"]
                assert data["services"]["minio"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_minio_unhealthy(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('app.api.v1.endpoints.health.SessionLocal') as mock_session_local, \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping') as mock_celery_ping, \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists') as mock_bucket_exists:

                mock_db_session_instance = MagicMock()
                mock_session_local.return_value = mock_db_session_instance
                mock_db_session_instance.__enter__.return_value = mock_db_session_instance

                mock_celery_ping.return_value = True
                mock_bucket_exists.side_effect = Exception("MinIO Connection Error")

                response = await client.get("/api/v1/health/")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert data["services"]["database"] == "healthy"
                assert data["services"]["redis"] == "healthy"
                assert "unhealthy: MinIO Connection Error" in data["services"]["minio"]

    @pytest.mark.asyncio
    async def test_health_check_all_unhealthy(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch('app.api.v1.endpoints.health.SessionLocal') as mock_session_local, \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping') as mock_celery_ping, \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists') as mock_bucket_exists:

                mock_db_session_instance = MagicMock()
                mock_session_local.return_value = mock_db_session_instance
                mock_db_session_instance.__enter__.return_value = mock_db_session_instance
                mock_db_session_instance.execute.side_effect = Exception("DB Error")

                mock_celery_ping.side_effect = Exception("Redis Error")
                mock_bucket_exists.side_effect = Exception("MinIO Error")

                response = await client.get("/api/v1/health/")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert "unhealthy: DB Error" in data["services"]["database"]
                assert "unhealthy: Redis Error" in data["services"]["redis"]
                assert "unhealthy: MinIO Error" in data["services"]["minio"]

    @pytest.mark.asyncio
    async def test_health_check_empty_path(self): # Removed client fixture
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test the "" path in the router
            with patch('app.api.v1.endpoints.health.SessionLocal'), \
                 patch('app.api.v1.endpoints.health.celery_app.control.ping'), \
                 patch('app.api.v1.endpoints.health.storage_service.client.bucket_exists'):
                # Assuming all healthy for this path check, default mock behaviors should be fine
                response = await client.get("/api/v1/health") # No trailing slash
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
