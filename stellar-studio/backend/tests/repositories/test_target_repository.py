# tests/repositories/test_target_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.target_repository import TargetRepository
from app.infrastructure.repositories.models.target import Target
from app.domain.value_objects.target_types import ObjectType, TargetStatus

@pytest.mark.asyncio
class TestTargetRepository:
    @pytest.fixture
    def mock_target(self):
        return Target(
            id=uuid4(),
            name="Nébuleuse du Papillon",
            catalog_name="NGC6302",
            common_name="Butterfly Nebula",
            coordinates_ra="17:13:44.21",
            coordinates_dec="-37:06:15.94",
            object_type=ObjectType.NEBULA,
            status=TargetStatus.READY,
            telescope_id=str(uuid4())
        )

    async def test_get_by_telescope(self, db_session, mock_target, configure_db_mock):
        # Arrange
        repo = TargetRepository(db_session)
        telescope_id = uuid4()
        mock_target.telescope_id = str(telescope_id)
        targets = [
            mock_target,
            Target(
                id=uuid4(),
                name="Galaxie d'Andromède",
                catalog_name="M31",
                coordinates_ra="00:42:44.3",
                coordinates_dec="+41:16:09",
                object_type=ObjectType.GALAXY,
                status=TargetStatus.READY,
                telescope_id=str(telescope_id)
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=targets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_telescope(telescope_id)
        
        # Assert
        assert len(result) == 2
        assert all(target.telescope_id == str(telescope_id) for target in result)

    async def test_get_by_status(self, db_session, mock_target, configure_db_mock):
        # Arrange
        repo = TargetRepository(db_session)
        status = TargetStatus.READY
        mock_target.status = status
        targets = [
            mock_target,
            Target(
                id=uuid4(),
                name="Galaxie du Tourbillon",
                catalog_name="M51",
                coordinates_ra="13:29:52.7",
                coordinates_dec="+47:11:43",
                object_type=ObjectType.GALAXY,
                status=status,
                telescope_id=str(uuid4())
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=targets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_status(status)
        
        # Assert
        assert len(result) == 2
        assert all(target.status == status for target in result)

    async def test_get_by_type(self, db_session, mock_target, configure_db_mock):
        # Arrange
        repo = TargetRepository(db_session)
        object_type = ObjectType.NEBULA
        mock_target.object_type = object_type
        targets = [
            mock_target,
            Target(
                id=uuid4(),
                name="Nébuleuse de l'Aigle",
                catalog_name="M16",
                coordinates_ra="18:18:48",
                coordinates_dec="-13:49:00",
                object_type=object_type,
                status=TargetStatus.READY,
                telescope_id=str(uuid4())
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=targets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_type(object_type)
        
        # Assert
        assert len(result) == 2
        assert all(target.object_type == object_type for target in result)

    async def test_get_by_name(self, db_session, mock_target, configure_db_mock):
        # Arrange
        repo = TargetRepository(db_session)
        name = "Nébuleuse du Papillon"
        mock_target.name = name
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_target)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_name(name)
        
        # Assert
        assert result is not None
        assert result.name == name

    async def test_get_by_name_not_found(self, db_session, configure_db_mock):
        # Arrange
        repo = TargetRepository(db_session)
        name = "Cible Inexistante"
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_name(name)
        
        # Assert
        assert result is None
