# tests/repositories/test_filter_repository.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.domain.models.filter import Filter 
from app.domain.value_objects.filter_types import FilterType
from app.infrastructure.repositories.filter_repository import FilterRepository

@pytest.mark.asyncio
class TestFilterRepository:
    async def test_create_filter(self, db_session):
        # Arrange
        repo = FilterRepository(db_session)
        filter_data = Filter(
            id=uuid4(),
            name="Test Filter",
            telescope_id=uuid4(),
            wavelength=500,
            filter_type=FilterType.BROADBAND,
            description="Un filtre de test"
        )
        
        # Configure mock
        db_session.execute = AsyncMock()
        db_session.execute.return_value = AsyncMock()
        db_session.execute.return_value.scalar_one = AsyncMock(return_value=filter_data)
        
        # Act
        created_filter = await repo.create(filter_data)
        
        # Assert
        assert created_filter.name == "Test Filter"
        assert created_filter.wavelength == 500
        db_session.add.assert_called_once_with(filter_data)
        db_session.commit.assert_called_once()

    async def test_get_by_telescope_and_type(self, db_session):
        # Arrange
        repo = FilterRepository(db_session)
        telescope_id = uuid4()
        filters = [
            Filter(id=uuid4(), name="F1", telescope_id=telescope_id, wavelength=500,
                  filter_type=FilterType.BROADBAND, description="Filtre 1"),
            Filter(id=uuid4(), name="F2", telescope_id=telescope_id, wavelength=600,
                  filter_type=FilterType.BROADBAND, description="Filtre 2")
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=filters)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_telescope_and_type(telescope_id, FilterType.BROADBAND)
        
        # Assert
        assert len(result) == 2
        assert all(f.telescope_id == telescope_id for f in result)
        assert all(f.filter_type == FilterType.BROADBAND for f in result)

    async def test_get_by_wavelength_range(self, db_session):
        # Arrange
        repo = FilterRepository(db_session)
        min_wave = 400
        max_wave = 600
        filters = [
            Filter(id=uuid4(), name="F1", telescope_id=uuid4(), wavelength=500,
                  filter_type=FilterType.BROADBAND, description="Filtre 1"),
            Filter(id=uuid4(), name="F2", telescope_id=uuid4(), wavelength=550,
                  filter_type=FilterType.NARROWBAND, description="Filtre 2")
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=filters)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_wavelength_range(min_wave, max_wave)
        
        # Assert
        assert len(result) == 2
        assert all(min_wave <= f.wavelength <= max_wave for f in result)
