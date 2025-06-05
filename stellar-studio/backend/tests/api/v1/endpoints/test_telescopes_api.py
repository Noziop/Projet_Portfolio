import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import os
import json
from typing import Optional, List, Dict, Any

# --- Pre-emptive Mocks for StorageService dependencies (and other global needs) ---
class MockSettingsGlobalTelescopesAPI:
    PROJECT_NAME: str = "Test Stellar Studio Telescopes API"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_telescopes_api.db"
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

patcher_minio_global_telescopes_api = patch('minio.Minio')
patcher_settings_global_telescopes_api = patch('app.core.config.settings', MockSettingsGlobalTelescopesAPI())
patcher_os_getenv_for_storage_telescopes_api = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_telescopes_api = patcher_minio_global_telescopes_api.start()
mock_settings_started_telescopes_api = patcher_settings_global_telescopes_api.start()
mock_os_getenv_for_storage_started_telescopes_api = patcher_os_getenv_for_storage_telescopes_api.start()

_global_minio_client_mock_instance_telescopes_api = MagicMock()
_global_minio_client_mock_instance_telescopes_api.bucket_exists.return_value = True
mock_minio_class_started_telescopes_api.return_value = _global_minio_client_mock_instance_telescopes_api
mock_os_getenv_for_storage_started_telescopes_api.return_value = 'mocked-bucket-at-import'

from app.main import app # Main FastAPI application
from app.schemas.user import User as UserSchema
from app.domain.models.user import UserRole
from app.api.deps import get_current_user
from app.schemas.telescope import TelescopeResponse
# from app.services.telescopes.service import TelescopeService as ActualTelescopeService # For spec if needed

def stop_global_patchers_telescopes_api():
    patcher_minio_global_telescopes_api.stop()
    patcher_settings_global_telescopes_api.stop()
    patcher_os_getenv_for_storage_telescopes_api.stop()

@pytest.fixture(scope="session", autouse=True)
def telescopes_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_telescopes_api)

# --- Mock TelescopeService Fixture ---
@pytest.fixture
def mock_telescope_service() -> MagicMock:
    service = MagicMock()
    service.get_telescopes = MagicMock()
    service.get_telescope = MagicMock()
    return service

# --- User Override Fixture ---
MOCK_USER_REGULAR_DATA = {
    "id": "user-regular-id", "email": "regular@example.com", "username": "regularuser",
    "firstname": "Regular", "lastname": "User", "level": "beginner", "role": UserRole.USER,
    "is_active": True, "created_at": "2023-01-01T12:00:00Z", "last_login": "2023-01-01T12:00:00Z"
}
MOCK_USER_REGULAR = UserSchema(**MOCK_USER_REGULAR_DATA)

@pytest.fixture
def authenticated_user_override():
    async def _override_get_current_user(): return MOCK_USER_REGULAR
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    if original: app.dependency_overrides[get_current_user] = original
    else: del app.dependency_overrides[get_current_user]


# Helper to create valid TelescopeResponse data for mocks
def _get_mock_telescope_response_data(id: str, name: str) -> Dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "description": f"Description for {name}",
        "aperture": "2.4m",
        "focal_length": "57.6m",
        "location": "Orbit",
        "instruments": json.dumps({"WFC3": "Camera", "COS": "Spectrograph"}), # Must be JSON string for model creation
        "api_endpoint": f"/api/v1/telescopes/{id}" # Example
    }

class TestPublicTelescopesEndpoints:
    BASE_URL = "/api/v1/telescopes"

    @pytest.mark.asyncio
    async def test_list_telescopes_success(self, mock_telescope_service: MagicMock, authenticated_user_override):
        mock_data_hst = _get_mock_telescope_response_data("HST", "Hubble Space Telescope")
        mock_data_jwst = _get_mock_telescope_response_data("JWST", "James Webb Space Telescope")

        # The service returns model instances
        mock_telescope_service.get_telescopes.return_value = [
            TelescopeResponse(**mock_data_hst),
            TelescopeResponse(**mock_data_jwst)
        ]

        with patch('app.api.v1.endpoints.telescopes.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/")

        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["id"] == "HST"
        assert response_data[1]["name"] == "James Webb Space Telescope"
        # Pydantic model dump will convert Json[Dict] (instruments) to dict
        assert isinstance(response_data[0]["instruments"], dict)
        mock_telescope_service.get_telescopes.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_telescopes_empty(self, mock_telescope_service: MagicMock, authenticated_user_override):
        mock_telescope_service.get_telescopes.return_value = []

        with patch('app.api.v1.endpoints.telescopes.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/")

        assert response.status_code == 200
        assert response.json() == []
        mock_telescope_service.get_telescopes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_telescope_success(self, mock_telescope_service: MagicMock, authenticated_user_override):
        telescope_id = "HST"
        mock_data = _get_mock_telescope_response_data(telescope_id, "Hubble Space Telescope")
        mock_telescope_service.get_telescope.return_value = TelescopeResponse(**mock_data)

        with patch('app.api.v1.endpoints.telescopes.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/{telescope_id}")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == telescope_id
        assert response_data["name"] == "Hubble Space Telescope"
        assert isinstance(response_data["instruments"], dict)
        mock_telescope_service.get_telescope.assert_called_once_with(telescope_id)

    @pytest.mark.asyncio
    async def test_get_telescope_not_found(self, mock_telescope_service: MagicMock, authenticated_user_override):
        telescope_id = "UNKNOWN"
        mock_telescope_service.get_telescope.return_value = None # Simulate not found

        with patch('app.api.v1.endpoints.telescopes.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"{self.BASE_URL}/{telescope_id}")

        assert response.status_code == 404
        assert response.json() == {"detail": "Telescope not found"}
        mock_telescope_service.get_telescope.assert_called_once_with(telescope_id)

    @pytest.mark.asyncio
    async def test_list_telescopes_no_auth(self):
        if get_current_user in app.dependency_overrides: # Ensure no auth override
            del app.dependency_overrides[get_current_user]
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"{self.BASE_URL}/")
        assert response.status_code == 401 # Due to router-level dependency
        assert "not authenticated" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_get_telescope_no_auth(self):
        telescope_id = "HST"
        if get_current_user in app.dependency_overrides: # Ensure no auth override
            del app.dependency_overrides[get_current_user]
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"{self.BASE_URL}/{telescope_id}")
        assert response.status_code == 401 # Due to router-level dependency
        assert "not authenticated" in response.json().get("detail", "").lower()
