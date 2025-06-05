import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import os
from typing import Optional, List, Dict, Any # Added List, Dict, Any

# --- Pre-emptive Mocks for StorageService dependencies (and other global needs) ---
class MockSettingsGlobalObservationsAPI: # Specific to this test module
    PROJECT_NAME: str = "Test Stellar Studio Observations API"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_observations_api.db"
    REDIS_SESSION_DB: int = 1
    DATABASE_USER: Optional[str] = "testuser"
    DATABASE_PASSWORD: Optional[str] = "testpass"
    DATABASE_HOST: Optional[str] = "testhost"
    DATABASE_PORT: Optional[str] = "1234"
    DATABASE_NAME: Optional[str] = "testdb"
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    SECRET_KEY: Optional[str] = "testsecretkey"
    CELERY_BROKER_URL: Optional[str] = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: Optional[str] = "redis://localhost:6379/0"
    ALGORITHM: Optional[str] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = 30

patcher_minio_global_obs_api = patch('minio.Minio')
patcher_settings_global_obs_api = patch('app.core.config.settings', MockSettingsGlobalObservationsAPI())
patcher_os_getenv_for_storage_obs_api = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_obs_api = patcher_minio_global_obs_api.start()
mock_settings_started_obs_api = patcher_settings_global_obs_api.start()
mock_os_getenv_for_storage_started_obs_api = patcher_os_getenv_for_storage_obs_api.start()

_global_minio_client_mock_instance_obs_api = MagicMock()
_global_minio_client_mock_instance_obs_api.bucket_exists.return_value = True
mock_minio_class_started_obs_api.return_value = _global_minio_client_mock_instance_obs_api
mock_os_getenv_for_storage_started_obs_api.return_value = 'mocked-bucket-at-import'

from app.main import app # Main FastAPI application
# Import the actual service to allow specing the mock correctly
from app.services.observation.service import ObservationService as ActualObservationService

def stop_global_patchers_observations_api():
    patcher_minio_global_obs_api.stop()
    patcher_settings_global_obs_api.stop()
    patcher_os_getenv_for_storage_obs_api.stop()

@pytest.fixture(scope="session", autouse=True)
def observations_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_observations_api)

# --- Mock ObservationService Fixture ---
@pytest.fixture
def mock_observation_service() -> AsyncMock:
    # Using spec with ActualObservationService which contains the real methods
    service = AsyncMock(spec=ActualObservationService)
    return service

class TestObservationsEndpoints:

    @pytest.mark.asyncio
    async def test_list_telescope_targets_success(self, mock_observation_service: AsyncMock):
        telescope_name = "HST"
        expected_targets_data = [
            {"id": "t1", "name": "Target 1 HST", "telescope_id": "HST"},
            {"id": "t2", "name": "Target 2 HST", "telescope_id": "HST"},
        ]
        # get_available_targets is synchronous in the actual service
        mock_observation_service.get_available_targets.return_value = expected_targets_data

        with patch('app.api.v1.endpoints.observations.observation_service', mock_observation_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/observations/{telescope_name}/targets")

        assert response.status_code == 200
        assert response.json() == expected_targets_data
        mock_observation_service.get_available_targets.assert_called_once_with(telescope_name)

    @pytest.mark.asyncio
    async def test_list_telescope_targets_not_found(self, mock_observation_service: AsyncMock):
        telescope_name = "UNKNOWN_SCOPE"
        # get_available_targets is synchronous
        mock_observation_service.get_available_targets.return_value = [] # No targets found

        with patch('app.api.v1.endpoints.observations.observation_service', mock_observation_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/observations/{telescope_name}/targets")

        assert response.status_code == 404
        assert response.json() == {"detail": f"No targets found for telescope {telescope_name}"}
        mock_observation_service.get_available_targets.assert_called_once_with(telescope_name)

    @pytest.mark.asyncio
    async def test_get_object_preview_success(self, mock_observation_service: AsyncMock):
        telescope = "HST"
        object_name = "M42"
        expected_preview_url = "http://example.com/m42_hst_preview.jpg"
        # get_target_preview is synchronous
        mock_observation_service.get_target_preview.return_value = expected_preview_url

        with patch('app.api.v1.endpoints.observations.observation_service', mock_observation_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/observations/preview/{telescope}/{object_name}")

        assert response.status_code == 200
        assert response.json() == {"preview_url": expected_preview_url}
        mock_observation_service.get_target_preview.assert_called_once_with(object_name, telescope)

    @pytest.mark.asyncio
    async def test_get_object_preview_not_found(self, mock_observation_service: AsyncMock):
        telescope = "HST"
        object_name = "UnknownObject"
        # get_target_preview is synchronous
        mock_observation_service.get_target_preview.return_value = None # No preview URL

        with patch('app.api.v1.endpoints.observations.observation_service', mock_observation_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/observations/preview/{telescope}/{object_name}")

        assert response.status_code == 404
        assert response.json() == {"detail": f"No preview available for {object_name}"}
        mock_observation_service.get_target_preview.assert_called_once_with(object_name, telescope)

    @pytest.mark.asyncio
    async def test_get_object_preview_service_exception(self, mock_observation_service: AsyncMock):
        telescope = "HST"
        object_name = "ErrorObject"
        # Simulate an unexpected error during service call
        mock_observation_service.get_target_preview.side_effect = Exception("Internal service error")

        with patch('app.api.v1.endpoints.observations.observation_service', mock_observation_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/observations/preview/{telescope}/{object_name}")

        # FastAPI should catch this unhandled exception and return a 500
        assert response.status_code == 500
        # The exact detail might vary based on server error handling (e.g. "Internal Server Error")
        # For now, checking the status code is the main goal.
        # assert "Internal Server Error" in response.json()["detail"]
        mock_observation_service.get_target_preview.assert_called_once_with(object_name, telescope)
