import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import os
from typing import Optional, List # Added List

# --- Pre-emptive Mocks for StorageService dependencies ---
class MockSettingsGlobal:
    PROJECT_NAME: str = "Test Stellar Studio"
    API_V1_STR: str = "/api/v1"
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test_temp_auth_api.db"
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

patcher_minio_global = patch('minio.Minio')
patcher_settings_global = patch('app.core.config.settings', MockSettingsGlobal())
patcher_os_getenv_for_storage = patch('app.services.storage.service.os.getenv')

mock_minio_class_started = patcher_minio_global.start()
mock_settings_started = patcher_settings_global.start()
mock_os_getenv_for_storage_started = patcher_os_getenv_for_storage.start()

_global_minio_client_mock_instance = MagicMock()
_global_minio_client_mock_instance.bucket_exists.return_value = True
mock_minio_class_started.return_value = _global_minio_client_mock_instance
mock_os_getenv_for_storage_started.return_value = 'mocked-bucket-at-import'

from app.main import app
from app.schemas.user import User as UserSchema, Token as TokenSchema, UserCreate, UserUpdate, PasswordChange
from app.services.auth.service import AuthService as ActualAuthService
from app.domain.models.user import UserRole
from app.api.deps import get_current_user
from fastapi import status, HTTPException # Added HTTPException

def stop_global_patchers_auth_api():
    patcher_minio_global.stop()
    patcher_settings_global.stop()
    patcher_os_getenv_for_storage.stop()

@pytest.fixture(scope="session", autouse=True)
def auth_api_module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers_auth_api)

# --- No shared client fixture, client created per test ---

# --- Mock AuthService Fixture ---
@pytest.fixture
def mock_auth_service() -> AsyncMock:
    service = AsyncMock(spec=ActualAuthService)
    # Methods that need to exist on the mock if not automatically created by spec (e.g. if original is not async)
    # For AuthService, most methods are async. 'change_password' is missing.
    # service.change_password = AsyncMock() # Add this if we were testing change_password
    return service

# --- User Override Fixtures ---
MOCK_USER_REGULAR_DATA = {
    "id": "user-regular-id", "email": "regular@example.com", "username": "regularuser",
    "firstname": "Regular", "lastname": "User", "level": "beginner", "role": UserRole.USER,
    "is_active": True, "created_at": "2023-01-01T12:00:00Z", "last_login": "2023-01-01T12:00:00Z"
}
MOCK_USER_ADMIN_DATA = {
    "id": "user-admin-id", "email": "admin@example.com", "username": "adminuser",
    "firstname": "Admin", "lastname": "User", "level": "advanced", "role": UserRole.ADMIN,
    "is_active": True, "created_at": "2023-01-01T11:00:00Z", "last_login": "2023-01-01T11:00:00Z"
}
MOCK_USER_REGULAR = UserSchema(**MOCK_USER_REGULAR_DATA)
MOCK_USER_ADMIN = UserSchema(**MOCK_USER_ADMIN_DATA)

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

@pytest.fixture
def admin_user_token_override():
    async def _override_get_current_user_admin():
        return MOCK_USER_ADMIN
    original_override = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = _override_get_current_user_admin
    yield
    if original_override:
        app.dependency_overrides[get_current_user] = original_override
    else:
        app.dependency_overrides.pop(get_current_user, None)


class TestAuthEndpoints:

    @pytest.mark.asyncio
    async def test_register_success(self, mock_auth_service: AsyncMock):
        user_create_data = {
            "email": "test@example.com", "username": "testuser",
            "password": "Password123!", "firstname": "Test", "lastname": "User", "level": "beginner"
        }
        expected_user_response_data = MOCK_USER_REGULAR.model_dump() # Use a full user model
        mock_auth_service.register_new_user.return_value = UserSchema(**expected_user_response_data)

        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/register", json=user_create_data)

        assert response.status_code == 200
        assert response.json()["email"] == expected_user_response_data["email"]
        mock_auth_service.register_new_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_failure_duplicate_email(self, mock_auth_service: AsyncMock):
        user_create_data = {"email": "existing@example.com", "username": "newuser", "password": "Password123!"}
        mock_auth_service.register_new_user.side_effect = ValueError("Email already registered")
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/register", json=user_create_data)
        assert response.status_code == 400
        assert response.json() == {"detail": "Email already registered"}

    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service: AsyncMock):
        expected_token_data = {"access_token": "fake-token", "token_type": "bearer"}
        mock_auth_service.authenticate.return_value = TokenSchema(**expected_token_data)
        login_data = {"username": "test@example.com", "password": "Password123!"}
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        assert response.json() == expected_token_data

    @pytest.mark.asyncio
    async def test_login_failure_invalid_credentials(self, mock_auth_service: AsyncMock):
        mock_auth_service.authenticate.side_effect = ValueError("Invalid email or password")
        login_data = {"username": "wrong@example.com", "password": "wrongpassword"}
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password"}

    @pytest.mark.asyncio
    async def test_read_current_user_me(self, regular_user_token_override):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == MOCK_USER_REGULAR.email

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_auth_service: AsyncMock, regular_user_token_override):
        mock_auth_service.logout.return_value = None
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json() == {"message": "Successfully logged out"}

    @pytest.mark.asyncio
    async def test_list_users_as_admin(self, mock_auth_service: AsyncMock, admin_user_token_override):
        mock_auth_service.list_all_users.return_value = [MOCK_USER_ADMIN, MOCK_USER_REGULAR]
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/auth/users")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_list_users_as_regular_user_forbidden(self, regular_user_token_override):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/users")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_register_invalid_input_bad_email(self, mock_auth_service: AsyncMock):
        user_create_data = {"email": "not-an-email", "username": "testuser", "password": "Password123!"}
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service): # Not strictly needed as it should fail before service call
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/register", json=user_create_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_me_no_token(self):
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    # Change password tests remain commented out
    # @pytest.mark.asyncio
    # async def test_change_password_success(self, mock_auth_service: AsyncMock, regular_user_token_override):
    #     # ...

    # @pytest.mark.asyncio
    # async def test_change_password_wrong_old(self, mock_auth_service: AsyncMock, regular_user_token_override):
    #     # ...

    @pytest.mark.asyncio
    async def test_deactivate_account_success(self, mock_auth_service: AsyncMock, regular_user_token_override):
        mock_auth_service.deactivate_account.return_value = True
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post("/api/v1/auth/deactivate")
        assert response.status_code == 200
        assert response.json() == {"message": "Account successfully deactivated"}

    @pytest.mark.asyncio
    async def test_get_user_by_id_admin_success(self, mock_auth_service: AsyncMock, admin_user_token_override):
        target_user_id = "some-user-id"
        mock_auth_service.get_user_by_id.return_value = MOCK_USER_REGULAR
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/auth/users/{target_user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == MOCK_USER_REGULAR.id

    @pytest.mark.asyncio
    async def test_get_user_by_id_admin_not_found(self, mock_auth_service: AsyncMock, admin_user_token_override):
        target_user_id = "unknown-user-id"
        mock_auth_service.get_user_by_id.return_value = None
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(f"/api/v1/auth/users/{target_user_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_admin_success(self, mock_auth_service: AsyncMock, admin_user_token_override):
        target_user_id = "user-to-update-id"
        update_data = {"firstname": "UpdatedFirst", "level": "intermediate"}
        updated_user_data = MOCK_USER_REGULAR.model_dump()
        updated_user_data.update({"firstname": "UpdatedFirst", "level": "intermediate"})
        mock_auth_service.update_user.return_value = UserSchema(**updated_user_data)
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.put(f"/api/v1/auth/users/{target_user_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["firstname"] == "UpdatedFirst"

    @pytest.mark.asyncio
    async def test_delete_user_admin_success(self, mock_auth_service: AsyncMock, admin_user_token_override):
        target_user_id = "user-to-delete-id"
        mock_auth_service.delete_user.return_value = True
        with patch('app.api.v1.endpoints.auth.auth_service', mock_auth_service):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.delete(f"/api/v1/auth/users/{target_user_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "User successfully deleted"}
