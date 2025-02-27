# tests/repositories/test_target_preset_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.target_preset_repository import TargetPresetRepository
from app.infrastructure.repositories.models.target_preset import TargetPreset
from app.infrastructure.repositories.models.preset_filter import PresetFilter
from app.infrastructure.repositories.models.target_file import TargetFile

@pytest.mark.asyncio
class TestTargetPresetRepository:
    @pytest.fixture
    def mock_target_preset(self):
        return TargetPreset(
            target_id=str(uuid4()),
            preset_id=str(uuid4()),
            is_available=True
        )

    async def test_get_by_target(self, db_session, mock_target_preset, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        mock_target_preset.target_id = str(target_id)
        target_presets = [
            mock_target_preset,
            TargetPreset(
                target_id=str(target_id),
                preset_id=str(uuid4()),
                is_available=False
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=target_presets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_target(target_id)
        
        # Assert
        assert len(result) == 2
        assert all(tp.target_id == str(target_id) for tp in result)

    async def test_get_by_preset(self, db_session, mock_target_preset, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        preset_id = uuid4()
        mock_target_preset.preset_id = str(preset_id)
        target_presets = [
            mock_target_preset,
            TargetPreset(
                target_id=str(uuid4()),
                preset_id=str(preset_id),
                is_available=True
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=target_presets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_preset(preset_id)
        
        # Assert
        assert len(result) == 2
        assert all(tp.preset_id == str(preset_id) for tp in result)

    async def test_update_availability_success(self, db_session, mock_target_preset, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        preset_id = uuid4()
        mock_target_preset.target_id = str(target_id)
        mock_target_preset.preset_id = str(preset_id)
        mock_target_preset.is_available = True
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_target_preset)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        success = await repo.update_availability(target_id, preset_id, False)
        
        # Assert
        assert success is True
        assert mock_target_preset.is_available is False
        db_session.commit.assert_called_once()

    async def test_update_availability_not_found(self, db_session, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        preset_id = uuid4()
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        success = await repo.update_availability(target_id, preset_id, True)
        
        # Assert
        assert success is False
        db_session.commit.assert_not_called()

    async def test_check_filters_availability_compatible(self, db_session, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        preset_id = uuid4()
        
        # Configurer le mock pour retourner une liste vide de filtres manquants
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=[])  # Aucun filtre manquant
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.check_filters_availability(target_id, preset_id)
        
        # Assert
        assert result is True
        db_session.execute.assert_called_once()

    async def test_check_filters_availability_incompatible(self, db_session, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        preset_id = uuid4()
        
        # Configurer le mock pour retourner une liste de filtres manquants
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=["missing_filter_id"])  # Un filtre manquant
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.check_filters_availability(target_id, preset_id)
        
        # Assert
        assert result is False
        db_session.execute.assert_called_once()

    async def test_check_filters_availability_no_required_filters(self, db_session, configure_db_mock):
        # Arrange
        repo = TargetPresetRepository(db_session)
        target_id = uuid4()
        preset_id = uuid4()
        
        # Configurer le mock pour retourner une liste vide (pas de filtres manquants car aucun requis)
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=[])  # Aucun filtre manquant
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.check_filters_availability(target_id, preset_id)
        
        # Assert
        assert result is True  # Si aucun filtre n'est manquant, tous les filtres requis sont disponibles
        db_session.execute.assert_called_once()
