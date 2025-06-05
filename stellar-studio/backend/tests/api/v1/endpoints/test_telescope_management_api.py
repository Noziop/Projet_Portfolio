import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
import os
import json # Ensure json is imported
from typing import Optional, List, Dict, Any

# --- Pre-emptive Mocks for StorageService dependencies (and other global needs) ---
class MockSettingsGlobalTelescopeMgmtAPI:
    PROJECT_NAME: str = "Test Stellar Studio TelescopeMgmt API"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_telescope_mgmt_api.db"
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

patcher_minio_global_tm_api = patch('minio.Minio')
patcher_settings_global_tm_api = patch('app.core.config.settings', MockSettingsGlobalTelescopeMgmtAPI())
patcher_os_getenv_for_storage_tm_api = patch('app.services.storage.service.os.getenv')

mock_minio_class_started_tm_api = patcher_minio_global_tm_api.start()
mock_settings_started_tm_api = patcher_settings_global_tm_api.start()
mock_os_getenv_for_storage_started_tm_api = patcher_os_getenv_for_storage_tm_api.start()

_global_minio_client_mock_instance_tm_api = MagicMock()
_global_minio_client_mock_instance_tm_api.bucket_exists.return_value = True
mock_minio_class_started_tm_api.return_value = _global_minio_client_mock_instance_tm_api
mock_os_getenv_for_storage_started_tm_api.return_value = 'mocked-bucket-at-import'

from app.main import app
from app.schemas.user import User as UserSchema
from app.domain.models.user import UserRole
from app.api.deps import get_current_user
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse

def stop_global_patchers_telescope_mgmt_api():
    patcher_minio_global_tm_api.stop()
    patcher_settings_global_tm_api.stop()
    patcher_os_getenv_for_storage_tm_api.stop()

@pytest.fixture(scope="session", autouse=True)
def telescope_mgmt_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_telescope_mgmt_api)

@pytest.fixture
def mock_telescope_service() -> MagicMock:
    service = MagicMock()
    service.create_telescope = MagicMock()
    service.update_telescope = MagicMock()
    service.get_telescope = MagicMock()
    service.delete_telescope = MagicMock()
    service.activate_telescope = MagicMock()
    service.deactivate_telescope = MagicMock()
    return service

MOCK_USER_BASE_DATA = {
    "firstname": "Test", "lastname": "User", "level": "beginner",
    "is_active": True, "created_at": "2023-01-01T12:00:00Z", "last_login": "2023-01-01T12:00:00Z"
}
MOCK_USER_ADMIN = UserSchema(id="admin-user-id", email="admin@example.com", username="adminuser", role=UserRole.ADMIN, **MOCK_USER_BASE_DATA)
MOCK_USER_OPERATOR = UserSchema(id="operator-user-id", email="operator@example.com", username="operatoruser", role=UserRole.OPERATOR, **MOCK_USER_BASE_DATA)
MOCK_USER_REGULAR = UserSchema(id="regular-user-id", email="regular@example.com", username="regularuser", role=UserRole.USER, **MOCK_USER_BASE_DATA)

@pytest.fixture
def admin_user_override():
    async def _override_get_current_user(): return MOCK_USER_ADMIN
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    if original: app.dependency_overrides[get_current_user] = original
    else: del app.dependency_overrides[get_current_user]

@pytest.fixture
def operator_user_override():
    async def _override_get_current_user(): return MOCK_USER_OPERATOR
    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    if original: app.dependency_overrides[get_current_user] = original
    else: del app.dependency_overrides[get_current_user]

class TestTelescopeManagementEndpoints:
    BASE_URL = "/api/v1/admin/telescopes" # Correct base URL for these endpoints

    # Helper to create valid TelescopeCreate data
    def _get_valid_telescope_create_data(self, id="HST-NG", name="Hubble Next Gen") -> Dict[str, Any]:
        return {
            "id": id, "name": name,
            "description": "A space telescope",
            "aperture": "2.4m", "focal_length": "57.6m", "location": "Orbit",
            # For request body to Pydantic model with Json[T], the field must be a JSON string
            "instruments": json.dumps({"WFC3": "Wide Field Camera 3", "COS": "Cosmic Origins Spectrograph"}),
            "api_endpoint": f"/api/v1/telescopes/{id}"
        }

    # Helper to create valid TelescopeResponse data for mocks
    def _get_mock_telescope_response_data(self, create_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": create_data["id"],
            "name": create_data["name"],
            "description": create_data.get("description"),
            "aperture": create_data["aperture"],
            "focal_length": create_data["focal_length"],
            "location": create_data["location"],
            # For TelescopeResponse model instantiation, if error says it needs string, provide string.
            # The create_data['instruments'] from _get_valid_telescope_create_data is already a JSON string.
            # If create_data comes from another source (like in update tests), ensure it's also a string.
            "instruments": create_data["instruments"] if isinstance(create_data["instruments"], str) else json.dumps(create_data["instruments"]),
            "api_endpoint": create_data["api_endpoint"]
        }

    @pytest.mark.asyncio
    async def test_create_telescope_as_admin_success(self, mock_telescope_service: MagicMock, admin_user_override):
        create_payload = self._get_valid_telescope_create_data()
        mock_response_data = self._get_mock_telescope_response_data(create_payload)
        mock_telescope_service.create_telescope.return_value = TelescopeResponse(**mock_response_data)

        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/", json=create_payload)

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["id"] == create_payload["id"]
        # Compare the 'instruments' field after parsing the JSON string from create_payload
        assert response_json["instruments"] == json.loads(create_payload["instruments"])
        mock_telescope_service.create_telescope.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_telescope_as_operator_forbidden(self, mock_telescope_service: MagicMock, operator_user_override):
        create_payload = self._get_valid_telescope_create_data(id="HST-FORBIDDEN")
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/", json=create_payload)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_telescope_service_value_error(self, mock_telescope_service: MagicMock, admin_user_override):
        create_payload = self._get_valid_telescope_create_data(id="HST-DUPLICATE")
        mock_telescope_service.create_telescope.side_effect = ValueError("Telescope ID already exists")
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/", json=create_payload)
        assert response.status_code == 400
        assert response.json() == {"detail": "Telescope ID already exists"}

    @pytest.mark.asyncio
    async def test_update_telescope_as_admin_success(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "HST"
        update_payload = {"name": "Hubble Updated", "description": "New description"} # Valid TelescopeUpdate fields

        mock_response_data = self._get_mock_telescope_response_data({
            "id": telescope_id, "name": update_payload["name"], "description": update_payload["description"],
            "aperture": "2.4m", "focal_length": "57.6m", "location": "Orbit",
            "instruments": {"WFC3": "Camera"}, "api_endpoint": f"/api/v1/telescopes/{telescope_id}"
        })
        mock_telescope_service.update_telescope.return_value = TelescopeResponse(**mock_response_data)

        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(f"{self.BASE_URL}/{telescope_id}", json=update_payload)

        assert response.status_code == 200
        assert response.json()["name"] == update_payload["name"]

    @pytest.mark.asyncio
    async def test_update_telescope_as_operator_success(self, mock_telescope_service: MagicMock, operator_user_override):
        telescope_id = "HST"
        update_payload = {"description": "Operator maintenance update."}

        mock_response_data = self._get_mock_telescope_response_data({
            "id": telescope_id, "name": "Hubble", "description": update_payload["description"],
            "aperture": "2.4m", "focal_length": "57.6m", "location": "Orbit",
            "instruments": {"WFC3": "Camera"}, "api_endpoint": f"/api/v1/telescopes/{telescope_id}"
        })
        mock_telescope_service.update_telescope.return_value = TelescopeResponse(**mock_response_data)

        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(f"{self.BASE_URL}/{telescope_id}", json=update_payload)
        assert response.status_code == 200
        assert response.json()["description"] == update_payload["description"]

    @pytest.mark.asyncio
    async def test_update_telescope_not_found(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "UNKNOWN"
        update_payload = {"name": "Unknown Updated"}
        mock_telescope_service.update_telescope.return_value = None
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(f"{self.BASE_URL}/{telescope_id}", json=update_payload)
        assert response.status_code == 404
        assert response.json()["detail"] == "Télescope non trouvé"

    @pytest.mark.asyncio
    async def test_delete_telescope_as_admin_success(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "HST"
        mock_telescope_service.get_telescope.return_value = MagicMock() # Simulate telescope exists
        mock_telescope_service.delete_telescope.return_value = True
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(f"{self.BASE_URL}/{telescope_id}")
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": f"Télescope {telescope_id} supprimé avec succès"}

    @pytest.mark.asyncio
    async def test_delete_telescope_not_found(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "UNKNOWN"
        mock_telescope_service.get_telescope.return_value = None
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(f"{self.BASE_URL}/{telescope_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Télescope non trouvé"

    @pytest.mark.asyncio
    async def test_deactivate_telescope_success(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "HST"
        mock_telescope_service.get_telescope.return_value = MagicMock()
        mock_telescope_service.deactivate_telescope.return_value = True
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/{telescope_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["message"] == f"Télescope {telescope_id} désactivé avec succès"

    @pytest.mark.asyncio
    async def test_activate_telescope_success(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "HST"
        mock_telescope_service.get_telescope.return_value = MagicMock()
        mock_telescope_service.activate_telescope.return_value = True
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/{telescope_id}/activate")
        assert response.status_code == 200
        assert response.json()["message"] == f"Télescope {telescope_id} activé avec succès"

    @pytest.mark.asyncio
    async def test_activate_telescope_failure_internal_error(self, mock_telescope_service: MagicMock, admin_user_override):
        telescope_id = "HST"
        mock_telescope_service.get_telescope.return_value = MagicMock()
        mock_telescope_service.activate_telescope.return_value = False
        with patch('app.api.v1.endpoints.telescope_management.telescope_service', mock_telescope_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(f"{self.BASE_URL}/{telescope_id}/activate")
        assert response.status_code == 500
        assert response.json() == {"detail": "Erreur lors de l'activation du télescope"}

    @pytest.mark.asyncio
    async def test_create_telescope_no_auth(self):
        create_payload = self._get_valid_telescope_create_data(id="HST-NOAUTH")
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(self.BASE_URL + "/", json=create_payload)
        assert response.status_code == 401
        assert "not authenticated" in response.json().get("detail", "").lower()
