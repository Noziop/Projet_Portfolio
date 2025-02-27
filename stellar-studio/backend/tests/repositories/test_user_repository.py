# tests/repositories/test_user_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.models.user import User
from app.domain.value_objects.user_types import UserRole, UserLevel

@pytest.mark.asyncio
class TestUserRepository:
    @pytest.fixture
    def mock_user(self):
        return User(
            id=uuid4(),
            email="test@stellarstudio.com",
            username="testuser",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # hash pour "password"
            firstname="Test",
            lastname="User",
            role=UserRole.USER,
            level=UserLevel.BEGINNER
        )

    async def test_get_by_email(self, db_session, mock_user, configure_db_mock):
        # Arrange
        repo = UserRepository(db_session)
        email = "test@stellarstudio.com"
        mock_user.email = email
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_email(email)
        
        # Assert
        assert result is not None
        assert result.email == email

    async def test_get_by_username(self, db_session, mock_user, configure_db_mock):
        # Arrange
        repo = UserRepository(db_session)
        username = "testuser"
        mock_user.username = username
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_username(username)
        
        # Assert
        assert result is not None
        assert result.username == username

    async def test_get_by_id(self, db_session, mock_user, configure_db_mock):
        # Arrange
        repo = UserRepository(db_session)
        user_id = mock_user.id
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_id(user_id)
        
        # Assert
        assert result is not None
        assert result.id == user_id
