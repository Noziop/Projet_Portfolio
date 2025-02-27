# tests/repositories/test_telescope_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.telescope_repository import TelescopeRepository
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.domain.value_objects.telescope_types import TelescopeStatus

@pytest.mark.asyncio
class TestTelescopeRepository:
    @pytest.fixture
    def mock_telescope(self):
        return SpaceTelescope(
            id=uuid4(),
            name="Hubble",
            aperture="2.4m",
            focal_length="57.6m",
            location="Low Earth Orbit",
            api_endpoint="https://api.hubble.nasa.gov",
            status=TelescopeStatus.ONLINE,
            instruments=[
                {"name": "WFC3", "type": "camera"},
                {"name": "COS", "type": "spectrograph"}
            ]
        )

    async def test_get_by_status(self, db_session, mock_telescope, configure_db_mock):
        # Arrange
        repo = TelescopeRepository(db_session)
        status = TelescopeStatus.ONLINE
        mock_telescope.status = status
        telescopes = [
            mock_telescope,
            SpaceTelescope(
                id=uuid4(),
                name="James Webb",
                aperture="6.5m",
                focal_length="131.4m",
                location="L2 Orbit",
                api_endpoint="https://api.jwst.nasa.gov",
                status=status,
                instruments=[{"name": "NIRCam", "type": "camera"}]
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=telescopes)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_status(status)
        
        # Assert
        assert len(result) == 2
        assert all(telescope.status == status for telescope in result)

    async def test_get_by_name(self, db_session, mock_telescope, configure_db_mock):
        # Arrange
        repo = TelescopeRepository(db_session)
        name = "Hubble"
        mock_telescope.name = name
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_telescope)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_name(name)
        
        # Assert
        assert result is not None
        assert result.name == name

    async def test_get_by_name_not_found(self, db_session, configure_db_mock):
        # Arrange
        repo = TelescopeRepository(db_session)
        name = "Télescope Inexistant"
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_name(name)
        
        # Assert
        assert result is None
