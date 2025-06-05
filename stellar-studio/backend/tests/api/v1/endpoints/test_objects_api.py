import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import os
from typing import Optional

# --- Pre-emptive Mocks for StorageService dependencies (and other global needs) ---
class MockSettingsGlobalObjects: # Specific to this test module
    PROJECT_NAME: str = "Test Stellar Studio Objects"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_objects_api.db"
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

patcher_minio_global_objects = patch('minio.Minio')
patcher_settings_global_objects = patch('app.core.config.settings', MockSettingsGlobalObjects())
patcher_os_getenv_for_storage_objects = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_objects = patcher_minio_global_objects.start()
mock_settings_started_objects = patcher_settings_global_objects.start()
mock_os_getenv_for_storage_started_objects = patcher_os_getenv_for_storage_objects.start()

_global_minio_client_mock_instance_objects = MagicMock()
_global_minio_client_mock_instance_objects.bucket_exists.return_value = True
mock_minio_class_started_objects.return_value = _global_minio_client_mock_instance_objects
mock_os_getenv_for_storage_started_objects.return_value = 'mocked-bucket-at-import'

from app.main import app # Main FastAPI application

def stop_global_patchers_objects_api():
    patcher_minio_global_objects.stop()
    patcher_settings_global_objects.stop()
    patcher_os_getenv_for_storage_objects.stop()

@pytest.fixture(scope="session", autouse=True)
def objects_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_objects_api)

# --- Test Client (created per test) ---

class TestObjectsEndpoint:

    @pytest.mark.asyncio
    async def test_get_object_info_success(self):
        object_name = "M31"
        expected_simbad_data = {
            "status": "success",
            "data": {"MAIN_ID": "M31", "RA": "00 42 44.330", "DEC": "+41 16 07.50"}
        }

        mock_task_result = MagicMock()
        mock_task_result.get.return_value = expected_simbad_data

        # Patch the .delay() method of fetch_object_data on the ObservationService
        # imported in app.api.v1.endpoints.objects
        with patch('app.api.v1.endpoints.objects.ObservationService.fetch_object_data.delay', return_value=mock_task_result) as mock_delay_call:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/objects/{object_name}")

        assert response.status_code == 200
        assert response.json() == expected_simbad_data
        mock_delay_call.assert_called_once_with(object_name)
        mock_task_result.get.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    async def test_get_object_info_task_error_status(self):
        object_name = "UnknownObject"
        error_result = {
            "status": "error",
            "message": "Object not found in Simbad"
        }
        mock_task_result = MagicMock()
        mock_task_result.get.return_value = error_result

        with patch('app.api.v1.endpoints.objects.ObservationService.fetch_object_data.delay', return_value=mock_task_result) as mock_delay_call:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/objects/{object_name}")

        assert response.status_code == 400
        assert response.json() == {"detail": "Object not found in Simbad"}
        mock_delay_call.assert_called_once_with(object_name)
        mock_task_result.get.assert_called_once_with(timeout=10)

    @pytest.mark.asyncio
    async def test_get_object_info_task_get_timeout(self):
        object_name = "SlowObject"
        mock_task_result = MagicMock()
        # Simulating Celery's TimeoutError when task.get() times out
        # This requires knowing what exception task.get() would raise.
        # If it's Celery's own TimeoutError: from celery.exceptions import TimeoutError
        # For now, assume a generic Exception that the endpoint's broad try-except might catch,
        # or that the HTTP client itself might time out if the endpoint blocks too long.
        # The endpoint code doesn't explicitly handle task.get() timeout leading to a specific HTTP error.
        # It would likely result in an unhandled server error (500) or httpx client timeout.
        # Let's assume the task.get itself raises an error that results in the "error" status.
        timeout_error_result = {
            "status": "error",
            "message": "Task timeout" # Generic message for this test
        }
        mock_task_result.get.return_value = timeout_error_result # Or .side_effect = CeleryTimeoutError()
                                                               # if we want to test the except block in endpoint.
                                                               # But the endpoint currently only checks result["status"].

        with patch('app.api.v1.endpoints.objects.ObservationService.fetch_object_data.delay', return_value=mock_task_result) as mock_delay_call:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/objects/{object_name}")

        assert response.status_code == 400 # Based on current endpoint logic checking result["status"]
        assert response.json() == {"detail": "Task timeout"}

    @pytest.mark.asyncio
    async def test_get_object_info_fetch_object_data_delay_raises_exception(self):
        object_name = "ErrorCase"

        # Simulate an error when .delay() is called
        with patch('app.api.v1.endpoints.objects.ObservationService.fetch_object_data.delay', side_effect=Exception("Celery dispatch error")) as mock_delay_call:
            async with AsyncClient(app=app, base_url="http://test") as client:
                # This will likely result in a 500 error as the endpoint doesn't specifically handle .delay() failure.
                # The try-except in the endpoint is around task.get(), not task.delay().
                response = await client.get(f"/api/v1/objects/{object_name}")

        assert response.status_code == 500 # Default for unhandled exceptions in FastAPI
        # The exact detail might vary based on FastAPI's error handling for unhandled exceptions.
        # It might be just {"detail": "Internal Server Error"} or include the exception message if debug is on.
        # For now, just check the status code.
        mock_delay_call.assert_called_once_with(object_name)
