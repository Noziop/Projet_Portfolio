import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import os
from typing import Optional

# --- Pre-emptive Mocks for StorageService dependencies (and other global needs) ---
class MockSettingsGlobalTasksAPI: # Specific to this test module
    PROJECT_NAME: str = "Test Stellar Studio Tasks API"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_tasks_api.db"
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

patcher_minio_global_tasks_api = patch('minio.Minio')
patcher_settings_global_tasks_api = patch('app.core.config.settings', MockSettingsGlobalTasksAPI())
patcher_os_getenv_for_storage_tasks_api = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_tasks_api = patcher_minio_global_tasks_api.start()
mock_settings_started_tasks_api = patcher_settings_global_tasks_api.start()
mock_os_getenv_for_storage_started_tasks_api = patcher_os_getenv_for_storage_tasks_api.start()

_global_minio_client_mock_instance_tasks_api = MagicMock()
_global_minio_client_mock_instance_tasks_api.bucket_exists.return_value = True
mock_minio_class_started_tasks_api.return_value = _global_minio_client_mock_instance_tasks_api
mock_os_getenv_for_storage_started_tasks_api.return_value = 'mocked-bucket-at-import'

from app.main import app # Main FastAPI application
from app.schemas.user import User as UserSchema # For get_current_user mock
from app.domain.models.user import UserRole # For get_current_user mock
from app.api.deps import get_current_user # To override this dependency
from app.schemas.task import DownloadRequest # Request model for /download

def stop_global_patchers_tasks_api():
    patcher_minio_global_tasks_api.stop()
    patcher_settings_global_tasks_api.stop()
    patcher_os_getenv_for_storage_tasks_api.stop()

@pytest.fixture(scope="session", autouse=True)
def tasks_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_tasks_api)

# --- Mock Services/Tasks Fixtures ---
@pytest.fixture
def mock_task_service_methods() -> MagicMock:
    # task_service.get_task_status is synchronous
    service_mock = MagicMock()
    service_mock.get_task_status = MagicMock()
    return service_mock

@pytest.fixture
def mock_download_fits_task() -> MagicMock:
    # download_fits.delay is what's called
    task_mock = MagicMock()
    task_mock.delay = MagicMock()
    return task_mock

# --- User Override Fixtures ---
MOCK_USER_REGULAR_DATA = { # Copied from test_auth_api, can be shared via conftest
    "id": "user-regular-id", "email": "regular@example.com", "username": "regularuser",
    "firstname": "Regular", "lastname": "User", "level": "beginner", "role": UserRole.USER,
    "is_active": True, "created_at": "2023-01-01T12:00:00Z", "last_login": "2023-01-01T12:00:00Z"
}
MOCK_USER_REGULAR = UserSchema(**MOCK_USER_REGULAR_DATA)

@pytest.fixture
def regular_user_token_override():
    async def _override_get_current_user_regular():
        return MOCK_USER_REGULAR
    original_override = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _override_get_current_user_regular
    yield
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
    else:
        app.dependency_overrides.pop(get_current_user, None)


class TestTasksEndpoints:

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, mock_task_service_methods: MagicMock):
        task_id = "some-task-id"
        expected_status = {"task_id": task_id, "status": "SUCCESS", "result": {"file_url": "http://example.com/file.fits"}}
        mock_task_service_methods.get_task_status.return_value = expected_status

        with patch('app.api.v1.endpoints.tasks.task_service', mock_task_service_methods):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200
        assert response.json() == expected_status
        mock_task_service_methods.get_task_status.assert_called_once_with(task_id)

    @pytest.mark.asyncio
    async def test_get_task_status_pending(self, mock_task_service_methods: MagicMock):
        task_id = "another-task-id"
        expected_status = {"task_id": task_id, "status": "PENDING", "result": None}
        mock_task_service_methods.get_task_status.return_value = expected_status

        with patch('app.api.v1.endpoints.tasks.task_service', mock_task_service_methods):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200
        assert response.json() == expected_status

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, mock_task_service_methods: MagicMock):
        task_id = "unknown-task-id"
        # Simulate task service raising an error or returning a specific "not found" marker
        # The endpoint doesn't show explicit error handling for get_task_status,
        # so we assume it returns what the service returns. If service raises, it'd be 500.
        # Let's assume service returns a dict indicating not found, as per typical Celery flower-like APIs.
        mock_task_service_methods.get_task_status.return_value = {"status": "FAILURE", "message": "Task not found"} # Or similar

        with patch('app.api.v1.endpoints.tasks.task_service', mock_task_service_methods):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200 # Endpoint itself doesn't raise HTTPException for this
        assert response.json()["status"] == "FAILURE"

    @pytest.mark.asyncio
    async def test_start_download_success(self, mock_download_fits_task: MagicMock, regular_user_token_override):
        download_request_data = {"object_name": "M31", "telescope": "HST"}

        mock_celery_task_instance = MagicMock()
        mock_celery_task_instance.id = "celery-task-id-123"
        mock_download_fits_task.delay.return_value = mock_celery_task_instance

        with patch('app.api.v1.endpoints.tasks.download_fits', mock_download_fits_task):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/tasks/download", json=download_request_data)

        assert response.status_code == 200
        assert response.json() == {"task_id": "celery-task-id-123"}
        mock_download_fits_task.delay.assert_called_once_with(
            object_name=download_request_data["object_name"],
            telescope=download_request_data["telescope"]
        )

    @pytest.mark.asyncio
    async def test_start_download_unauthenticated(self):
        # No regular_user_token_override, so get_current_user should raise default 401/403
        if get_current_user in app.dependency_overrides: # Ensure no accidental override
            del app.dependency_overrides[get_current_user]

        download_request_data = {"object_name": "M31", "telescope": "HST"}
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/tasks/download", json=download_request_data)

        assert response.status_code == 401
        assert "not authenticated" in response.json().get("detail","").lower() # Made assertion lowercase

    @pytest.mark.asyncio
    async def test_start_download_celery_delay_error(self, mock_download_fits_task: MagicMock, regular_user_token_override):
        download_request_data = {"object_name": "M31", "telescope": "HST"}
        mock_download_fits_task.delay.side_effect = Exception("Celery connection error")

        with patch('app.api.v1.endpoints.tasks.download_fits', mock_download_fits_task):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/tasks/download", json=download_request_data)

        assert response.status_code == 500 # Unhandled exception in endpoint
        # Detail might be "Internal Server Error" or include the exception message
        # assert "Celery connection error" in response.json()["detail"]
        mock_download_fits_task.delay.assert_called_once_with(
            object_name=download_request_data["object_name"],
            telescope=download_request_data["telescope"]
        )

    @pytest.mark.asyncio
    async def test_start_download_invalid_request_body(self, mock_download_fits_task: MagicMock, regular_user_token_override): # Added fixtures
        # Missing 'telescope' field
        download_request_data = {"object_name": "M31"}
        # Patch download_fits even if not expected to be called, to ensure endpoint setup is complete if reached
        with patch('app.api.v1.endpoints.tasks.download_fits', mock_download_fits_task):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/tasks/download", json=download_request_data)

        assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
        response_data = response.json()
        assert any(err["type"] == "missing" and "telescope" in err["loc"] for err in response_data.get("detail", []))
