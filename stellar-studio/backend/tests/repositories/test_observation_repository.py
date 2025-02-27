# tests/repositories/test_observation_repository.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4
from app.infrastructure.repositories.models.observation import Observation
from app.infrastructure.repositories.models.target import Target
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.infrastructure.repositories.observation_repository import ObservationRepository
from app.domain.value_objects.target_types import ObjectType, TargetStatus
from app.domain.value_objects.telescope_types import TelescopeStatus

@pytest.mark.asyncio
class TestObservationRepository:
    @pytest.fixture
    def mock_target(self):
        return Target(
            id=uuid4(),
            name="Test Target",
            description="Test Description",
            catalog_name="NGC1234",
            common_name="Test Object",
            coordinates_ra="00:00:00",
            coordinates_dec="+00:00:00",
            object_type=ObjectType.NEBULA,
            status=TargetStatus.NEEDS_DOWNLOAD
        )

    @pytest.fixture
    def mock_telescope(self):
        return SpaceTelescope(
            id=uuid4(),
            name="Test Telescope",
            description="Test Description",
            aperture="2.4m",
            focal_length="57.6m",
            location="L2",
            status=TelescopeStatus.ONLINE,
            api_endpoint="http://test.com",
            instruments=[]
        )

    async def test_create_observation(self, db_session, mock_target, mock_telescope):
        # Arrange
        repo = ObservationRepository(db_session)
        observation = Observation(
            id=uuid4(),
            target_id=mock_target.id,
            telescope_id=mock_telescope.id,
            observation_date=datetime.now(timezone.utc),
            exposure_time=120.0
        )
        
        # Configure mock
        db_session.execute = AsyncMock()
        db_session.execute.return_value = AsyncMock()
        db_session.execute.return_value.scalar_one = AsyncMock(return_value=observation)
        
        # Act
        created_observation = await repo.create(observation)
        
        # Assert
        assert created_observation.id == observation.id
        assert created_observation.exposure_time == 120.0
        db_session.add.assert_called_once_with(observation)
        db_session.commit.assert_called_once()

    async def test_get_by_target(self, db_session, mock_target, mock_telescope):
        # Arrange
        repo = ObservationRepository(db_session)
        observations = [
            Observation(
                id=uuid4(),
                target_id=mock_target.id,
                telescope_id=mock_telescope.id,
                observation_date=datetime.now(timezone.utc),
                exposure_time=120.0
            ),
            Observation(
                id=uuid4(),
                target_id=mock_target.id,
                telescope_id=mock_telescope.id,
                observation_date=datetime.now(timezone.utc),
                exposure_time=180.0
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=observations)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_target(mock_target.id)
        
        # Assert
        assert len(result) == 2
        assert all(obs.target_id == mock_target.id for obs in result)

    async def test_get_latest_by_target(self, db_session, mock_target, mock_telescope):
        # Arrange
        repo = ObservationRepository(db_session)
        observation = Observation(
            id=uuid4(),
            target_id=mock_target.id,
            telescope_id=mock_telescope.id,
            observation_date=datetime.now(timezone.utc),
            exposure_time=120.0
        )
        
        # Configure mock
        db_session.execute = AsyncMock()
        db_session.execute.return_value = AsyncMock()
        db_session.execute.return_value.scalar_one_or_none = AsyncMock(return_value=observation)
        
        # Act
        result = await repo.get_latest_by_target(mock_target.id)
        
        # Assert
        assert result is not None
        assert result.target_id == mock_target.id

    async def test_get_by_date_range(self, db_session, mock_target, mock_telescope):
        # Arrange
        repo = ObservationRepository(db_session)
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 12, 31, tzinfo=timezone.utc)
        observations = [
            Observation(
                id=uuid4(),
                target_id=mock_target.id,
                telescope_id=mock_telescope.id,
                observation_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
                exposure_time=120.0
            ),
            Observation(
                id=uuid4(),
                target_id=mock_target.id,
                telescope_id=mock_telescope.id,
                observation_date=datetime(2024, 7, 1, tzinfo=timezone.utc),
                exposure_time=180.0
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=observations)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_date_range(start_date, end_date)
        
        # Assert
        assert len(result) == 2
        assert all(start_date <= obs.observation_date <= end_date for obs in result)
