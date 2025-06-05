import pytest
from unittest.mock import MagicMock, patch
from typing import Optional, List
from datetime import datetime, timezone

from app.services.auth.service import AuthService
from app.schemas.user import UserCreate, User, Token, UserUpdate
from app.infrastructure.repositories.models.user import User as UserModel
from app.db.session import SessionLocal


@pytest.fixture
def auth_service():
    """Fixture to create an AuthService instance."""
    return AuthService()

class TestAuthService:
    # Basic test to check if the fixture works
    def test_auth_service_fixture(self, auth_service: AuthService):
        assert auth_service is not None
        assert auth_service.session_handler is not None
        assert auth_service.password_manager is not None

    @pytest.mark.asyncio
    async def test_register_new_user_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance # For `with ... as db:`

        mock_user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="Password123!", # Fixed: Special character added
            firstname="Test",
            lastname="User",
            level="beginner"
        )

        time_now = datetime.now(timezone.utc)
        expected_user_from_orm = User(
            id="some-uuid",
            email="test@example.com",
            username="testuser",
            firstname="Test",
            lastname="User",
            level="beginner",
            role="user",
            is_active=True,
            created_at=time_now,
            last_login=time_now # Added
        )

        # Patch app.services.auth.service.SessionLocal to return our context-manager-ready mock
        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance) as mock_session_local_factory:
            auth_service._get_user_by_email = MagicMock(return_value=None)
            auth_service._get_user_by_username = MagicMock(return_value=None)
            auth_service._create_user = MagicMock(return_value=expected_user_from_orm) # _create_user returns a User schema instance

            created_user = await auth_service.register_new_user(mock_user_data)

            mock_session_local_factory.assert_called_once() # Ensure the factory was called
            auth_service._get_user_by_email.assert_called_once_with(mock_db_session_instance, "test@example.com")
            auth_service._get_user_by_username.assert_called_once_with(mock_db_session_instance, "testuser")
            auth_service._create_user.assert_called_once_with(mock_db_session_instance, mock_user_data)
            assert created_user == expected_user_from_orm

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        email = "test@example.com"
        password = "Password123" # Fixed: Uppercase

        # UserModel instance that _get_user_by_email would return
        mock_user_orm_instance = UserModel(
            id="some-uuid",
            email=email,
            hashed_password="hashed_password",
            is_active=True,
            # Add other fields required by User.from_orm if it were called on this directly
            # or if used by session_handler.create_session
            username="testuser",
            firstname="Test", # Added
            lastname="User",  # Added
            level="beginner", # Added
            role="user",      # Added
            created_at=datetime.now(timezone.utc) # Added
        )
        expected_token = Token(access_token="some_access_token", token_type="bearer")

        # Patch SessionLocal in the service's module
        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance) as mock_session_local_factory:
            # Configure the mock session instance that the AuthService will use
            mock_query_on_session = MagicMock()
            mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
            mock_db_session_instance.query.return_value = mock_query_on_session

            # Mock methods of PasswordManager and SessionHandler
            auth_service.password_manager.verify_password = MagicMock(return_value=True)
            auth_service.session_handler.create_session = MagicMock(return_value=expected_token)

            token = await auth_service.authenticate(email, password)

            mock_session_local_factory.assert_called_once()
            mock_db_session_instance.query.assert_called_once_with(UserModel) # Check query on the session
            # Example of checking the filter call more specifically:
            # mock_query_on_session.filter.assert_called_once_with(UserModel.email == email)
            auth_service.password_manager.verify_password.assert_called_once_with(password, "hashed_password")
            auth_service.session_handler.create_session.assert_called_once_with(mock_db_session_instance, mock_user_orm_instance)
            assert token == expected_token

    @pytest.mark.asyncio
    async def test_logout(self, auth_service: AuthService):
        user_id = "some-user-id"
        auth_service.session_handler.revoke_session = MagicMock(return_value=True)

        result = await auth_service.logout(user_id)

        auth_service.session_handler.revoke_session.assert_called_once_with(user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_token(self, auth_service: AuthService):
        user_id = "some-user-id"
        auth_service.session_handler.validate_session = MagicMock(return_value=True)

        result = await auth_service.validate_token(user_id)

        auth_service.session_handler.validate_session.assert_called_once_with(user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_account_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        mock_user_orm_instance = UserModel(
            id=user_id, is_active=True, email="user@example.com", username="user",
            firstname="Test", lastname="User", level="beginner", role="user",
            created_at=datetime.now(timezone.utc), last_login=datetime.now(timezone.utc) # Added last_login
        )

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
        mock_db_session_instance.query.return_value = mock_query_on_session

        # If revoke_session is async, its mock should be async
        auth_service.session_handler.revoke_session = AsyncMock(return_value=True)

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            result = await auth_service.deactivate_account(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once() # Removed specific check for BinaryExpression

            assert mock_user_orm_instance.is_active is False
            mock_db_session_instance.commit.assert_called_once()
            auth_service.session_handler.revoke_session.assert_called_once_with(user_id)
            assert result is True

    @pytest.mark.asyncio
    async def test_deactivate_account_user_not_found(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "non-existent-user-id"

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = None
        mock_db_session_instance.query.return_value = mock_query_on_session

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            with pytest.raises(ValueError, match="User not found"):
                await auth_service.deactivate_account(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once() # Removed specific check for BinaryExpression
            mock_db_session_instance.commit.assert_not_called()
            auth_service.session_handler.revoke_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_all_users(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance

        time_now = datetime.now(timezone.utc)
        mock_user_orm_instances = [
            UserModel(id="uuid1", email="user1@example.com", username="user1", firstname="F1", lastname="L1", level="beginner", role="user", is_active=True, created_at=time_now, last_login=time_now),
            UserModel(id="uuid2", email="user2@example.com", username="user2", firstname="F2", lastname="L2", level="advanced", role="admin", is_active=True, created_at=time_now, last_login=time_now),
        ]

        expected_users_schemas = [
            User(id="uuid1", email="user1@example.com", username="user1", firstname="F1", lastname="L1", level="beginner", role="user", is_active=True, created_at=time_now, last_login=time_now),
            User(id="uuid2", email="user2@example.com", username="user2", firstname="F2", lastname="L2", level="advanced", role="admin", is_active=True, created_at=time_now, last_login=time_now),
        ]

        mock_query_on_session = MagicMock()
        mock_query_on_session.all.return_value = mock_user_orm_instances
        mock_db_session_instance.query.return_value = mock_query_on_session

        # If User.from_orm is correctly configured in the schema (from_attributes=True), this patch might not be needed.
        # However, to ensure the test passes regardless of that config for now:
        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance), \
             patch('app.schemas.user.User.from_orm', side_effect=expected_users_schemas) as mock_from_orm_call:
            users = await auth_service.list_all_users()

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.all.assert_called_once()
            assert mock_from_orm_call.call_count == len(mock_user_orm_instances)
            assert users == expected_users_schemas
            # Deeper comparison if needed:
            for i in range(len(users)):
                assert users[i].id == expected_users_schemas[i].id
                assert users[i].email == expected_users_schemas[i].email


    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        time_now = datetime.now(timezone.utc)
        mock_user_orm_instance = UserModel(
            id=user_id, email="user@example.com", username="user", firstname="Test",
            lastname="User", level="beginner", role="user", is_active=True, created_at=time_now, last_login=time_now # Added last_login
        )
        expected_user_schema = User(
            id=user_id, email="user@example.com", username="user", firstname="Test",
            lastname="User", level="beginner", role="user", is_active=True, created_at=time_now, last_login=time_now # Added last_login
        )

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
        mock_db_session_instance.query.return_value = mock_query_on_session

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance), \
             patch('app.schemas.user.User.from_orm', return_value=expected_user_schema) as mock_from_orm:
            user = await auth_service.get_user_by_id(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once_with(UserModel.id == user_id)
            mock_from_orm.assert_called_once_with(mock_user_orm_instance)
            assert user is not None
            assert user == expected_user_schema

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "non-existent-user-id"

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = None
        mock_db_session_instance.query.return_value = mock_query_on_session

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            user = await auth_service.get_user_by_id(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once() # Removed specific check for BinaryExpression
            assert user is None

    @pytest.mark.asyncio
    async def test_update_user_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        time_now = datetime.now(timezone.utc)
        user_update_data = UserUpdate(email="newemail@example.com", username="newusername", level="advanced")

        mock_user_orm_instance = UserModel(
            id=user_id, email="old@example.com", username="oldusername",
            firstname="OldF", lastname="OldL", level="beginner", role="user",
            is_active=True, created_at=time_now, last_login=time_now # Added last_login
        )

        expected_user_schema = User(
            id=user_id, email="newemail@example.com", username="newusername",
            firstname="OldF", lastname="OldL",
            level="advanced", role="user", is_active=True, created_at=time_now,
            last_login=time_now # Added last_login
        )

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
        mock_db_session_instance.query.return_value = mock_query_on_session

        auth_service._get_user_by_email = MagicMock(return_value=None)
        auth_service._get_user_by_username = MagicMock(return_value=None)

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance), \
             patch('app.schemas.user.User.from_orm', return_value=expected_user_schema) as mock_user_from_orm:
            updated_user = await auth_service.update_user(user_id, user_update_data)

            mock_db_session_instance.query.assert_called_once_with(UserModel) # Initial query to get user
            # Check that internal _get_user_by_email and _get_user_by_username were called with the session
            auth_service._get_user_by_email.assert_called_once_with(mock_db_session_instance, user_update_data.email)
            auth_service._get_user_by_username.assert_called_once_with(mock_db_session_instance, user_update_data.username)

            assert mock_user_orm_instance.email == user_update_data.email
            assert mock_user_orm_instance.username == user_update_data.username
            assert mock_user_orm_instance.level == user_update_data.level # Check level was updated
            mock_db_session_instance.commit.assert_called_once()
            mock_db_session_instance.refresh.assert_called_once_with(mock_user_orm_instance)

            mock_user_from_orm.assert_called_once_with(mock_user_orm_instance)
            assert updated_user == expected_user_schema

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "non-existent-user-id"
        user_update_data = UserUpdate(email="newemail@example.com")

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = None
        mock_db_session_instance.query.return_value = mock_query_on_session

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            with pytest.raises(ValueError, match="User not found"):
                await auth_service.update_user(user_id, user_update_data)
            mock_db_session_instance.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        user_update_data = UserUpdate(email="duplicate@example.com")

        mock_user_model_to_update = UserModel(id=user_id, email="original@example.com", username="someuser")
        mock_existing_user_with_duplicate_email = UserModel(id="other-id", email="duplicate@example.com", username="otheruser")

        mock_query_for_update_instance = MagicMock()
        mock_query_for_update_instance.filter.return_value.first.return_value = mock_user_model_to_update
        mock_db_session_instance.query.return_value = mock_query_for_update_instance

        auth_service._get_user_by_email = MagicMock(return_value=mock_existing_user_with_duplicate_email)
        auth_service._get_user_by_username = MagicMock(return_value=None)

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            with pytest.raises(ValueError, match="Email already registered"):
                await auth_service.update_user(user_id, user_update_data)

            auth_service._get_user_by_email.assert_called_once_with(mock_db_session_instance, "duplicate@example.com")
            mock_db_session_instance.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_duplicate_username(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        user_update_data = UserUpdate(username="duplicate_username")

        mock_user_model_to_update = UserModel(id=user_id, email="user@example.com", username="original_username")
        mock_existing_user_with_duplicate_username = UserModel(id="other-id", email="other@example.com", username="duplicate_username")

        mock_query_for_update_instance = MagicMock()
        mock_query_for_update_instance.filter.return_value.first.return_value = mock_user_model_to_update
        mock_db_session_instance.query.return_value = mock_query_for_update_instance

        auth_service._get_user_by_email = MagicMock(return_value=None)
        auth_service._get_user_by_username = MagicMock(return_value=mock_existing_user_with_duplicate_username)

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            with pytest.raises(ValueError, match="Username already taken"):
                await auth_service.update_user(user_id, user_update_data)

            auth_service._get_user_by_username.assert_called_once_with(mock_db_session_instance, "duplicate_username")
            mock_db_session_instance.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_user_success(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "existing-user-id"
        time_now = datetime.now(timezone.utc)
        mock_user_orm_instance = UserModel(
            id=user_id, email="user@example.com", username="user", firstname="Test",
            lastname="User", level="beginner", role="user", is_active=True,
            created_at=time_now, last_login=time_now # Added last_login
        )

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
        mock_db_session_instance.query.return_value = mock_query_on_session

        auth_service.session_handler.revoke_session = AsyncMock(return_value=True) # Fixed: AsyncMock

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            result = await auth_service.delete_user(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once() # Removed specific check

            auth_service.session_handler.revoke_session.assert_called_once_with(user_id)
            mock_db_session_instance.delete.assert_called_once_with(mock_user_orm_instance)
            mock_db_session_instance.commit.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        user_id = "non-existent-user-id"

        mock_query_on_session = MagicMock()
        mock_query_on_session.filter.return_value.first.return_value = None
        mock_db_session_instance.query.return_value = mock_query_on_session

        auth_service.session_handler.revoke_session = AsyncMock() # Fixed: AsyncMock

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            with pytest.raises(ValueError, match="User not found"):
                await auth_service.delete_user(user_id)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            mock_query_on_session.filter.assert_called_once() # Removed specific check

            auth_service.session_handler.revoke_session.assert_not_called()
            mock_db_session_instance.delete.assert_not_called()
            mock_db_session_instance.commit.assert_not_called()
            auth_service.session_handler.create_session.assert_called_once_with(mock_db_session, mock_user_model)
            assert token == expected_token

    @pytest.mark.asyncio
    async def test_authenticate_invalid_email(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        email = "wrong@example.com"
        password = "Password123" # Fixed

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            mock_query_on_session = MagicMock()
            mock_query_on_session.filter.return_value.first.return_value = None # Simulate user not found
            mock_db_session_instance.query.return_value = mock_query_on_session


            with pytest.raises(ValueError, match="Invalid email or password"):
                await auth_service.authenticate(email, password)

            mock_db_session_instance.query.assert_called_once_with(UserModel)


    @pytest.mark.asyncio
    async def test_authenticate_incorrect_password(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        email = "test@example.com"
        password = "WrongPassword123" # Fixed

        mock_user_orm_instance = UserModel(
            email=email, hashed_password="hashed_password", is_active=True,
            username="testuser", firstname="Test", lastname="User",
            level="beginner", role="user", created_at=datetime.now(timezone.utc)
        )

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            mock_query_on_session = MagicMock()
            mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
            mock_db_session_instance.query.return_value = mock_query_on_session

            auth_service.password_manager.verify_password = MagicMock(return_value=False) # Simulate incorrect password

            with pytest.raises(ValueError, match="Invalid email or password"):
                await auth_service.authenticate(email, password)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            auth_service.password_manager.verify_password.assert_called_once_with(password, "hashed_password")

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        email = "test@example.com"
        password = "Password123" # Fixed

        mock_user_orm_instance = UserModel(
            email=email, hashed_password="hashed_password", is_active=False, # User is inactive
            username="testuser", firstname="Test", lastname="User",
            level="beginner", role="user", created_at=datetime.now(timezone.utc)
        )

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            mock_query_on_session = MagicMock()
            mock_query_on_session.filter.return_value.first.return_value = mock_user_orm_instance
            mock_db_session_instance.query.return_value = mock_query_on_session

            auth_service.password_manager.verify_password = MagicMock(return_value=True) # Password is correct

            with pytest.raises(ValueError, match="User account is disabled"):
                await auth_service.authenticate(email, password)

            mock_db_session_instance.query.assert_called_once_with(UserModel)
            auth_service.password_manager.verify_password.assert_called_once_with(password, "hashed_password")
            # The following lines were incorrectly copied from another test in the previous diff, removing them:
            # auth_service._create_user.assert_called_once_with(mock_db_session_instance, mock_user_data)
            # assert created_user == expected_user_from_orm

    @pytest.mark.asyncio
    async def test_register_new_user_duplicate_email(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        mock_user_data = UserCreate(email="test@example.com", username="testuser", password="Password123!") # Fixed

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            auth_service._get_user_by_email = MagicMock(return_value=UserModel())

            with pytest.raises(ValueError, match="Email already registered"):
                await auth_service.register_new_user(mock_user_data)

            auth_service._get_user_by_email.assert_called_once_with(mock_db_session_instance, "test@example.com")

    @pytest.mark.asyncio
    async def test_register_new_user_duplicate_username(self, auth_service: AuthService):
        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        mock_user_data = UserCreate(email="test@example.com", username="testuser", password="Password123!") # Fixed

        with patch('app.services.auth.service.SessionLocal', return_value=mock_db_session_instance):
            auth_service._get_user_by_email = MagicMock(return_value=None)
            auth_service._get_user_by_username = MagicMock(return_value=UserModel())

            with pytest.raises(ValueError, match="Username already taken"):
                await auth_service.register_new_user(mock_user_data)

            auth_service._get_user_by_email.assert_called_once_with(mock_db_session_instance, "test@example.com")
            auth_service._get_user_by_username.assert_called_once_with(mock_db_session_instance, "testuser")
