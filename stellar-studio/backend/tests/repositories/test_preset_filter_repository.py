# tests/repositories/test_preset_filter_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.preset_filter_repository import PresetFilterRepository
from app.infrastructure.repositories.models.preset_filter import PresetFilter

@pytest.mark.asyncio
class TestPresetFilterRepository:
    @pytest.fixture
    def mock_preset_filter(self):
        return PresetFilter(
            preset_id=str(uuid4()),
            filter_id=str(uuid4()),
            order=0
        )

    async def test_create_preset_filter(self, db_session, mock_preset_filter, configure_db_mock):
        # Arrange
        repo = PresetFilterRepository(db_session)
        
        # Configure mock
        configure_db_mock(db_session, mock_preset_filter)
        
        # Act
        created_filter = await repo.create(mock_preset_filter)
        
        # Assert
        assert created_filter.preset_id == mock_preset_filter.preset_id
        assert created_filter.filter_id == mock_preset_filter.filter_id
        assert created_filter.order == 0
        db_session.add.assert_called_once_with(mock_preset_filter)
        db_session.commit.assert_called_once()

    async def test_get_by_preset(self, db_session, mock_preset_filter, configure_db_mock):
        # Arrange
        repo = PresetFilterRepository(db_session)
        preset_filters = [
            mock_preset_filter,
            PresetFilter(
                preset_id=mock_preset_filter.preset_id,
                filter_id=str(uuid4()),
                order=1
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=preset_filters)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_preset(mock_preset_filter.preset_id)
        
        # Assert
        assert len(result) == 2
        assert all(pf.preset_id == mock_preset_filter.preset_id for pf in result)

    async def test_get_by_filter(self, db_session, mock_preset_filter, configure_db_mock):
        # Arrange
        repo = PresetFilterRepository(db_session)
        preset_filters = [
            mock_preset_filter,
            PresetFilter(
                preset_id=str(uuid4()),
                filter_id=mock_preset_filter.filter_id,
                order=1
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=preset_filters)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_filter(mock_preset_filter.filter_id)
        
        # Assert
        assert len(result) == 2
        assert all(pf.filter_id == mock_preset_filter.filter_id for pf in result)

