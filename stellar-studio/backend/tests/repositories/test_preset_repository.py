# tests/repositories/test_preset_repository.py
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.models.preset import Preset

@pytest.mark.asyncio
class TestPresetRepository:
    @pytest.fixture
    def mock_preset(self):
        return Preset(
            id=uuid4(),
            name="Test Preset",
            description="Test Description",
            telescope_id=str(uuid4()),
            target_type="nebula",
            processing_params={
                "version": "1.0",
                "steps": [
                    {"name": "stretch", "params": {"factor": 1.5}},
                    {"name": "denoise", "params": {"strength": 0.5}}
                ]
            }
        )

    async def test_create_preset(self, db_session, mock_preset, configure_db_mock):
        # Arrange
        repo = PresetRepository(db_session)
        
        # Configure mock
        configure_db_mock(db_session, mock_preset)
        
        # Act
        created_preset = await repo.create(mock_preset)
        
        # Assert
        assert created_preset.id == mock_preset.id
        assert created_preset.name == "Test Preset"
        assert created_preset.processing_params["version"] == "1.0"
        db_session.add.assert_called_once_with(mock_preset)
        db_session.commit.assert_called_once()

    async def test_get_by_telescope(self, db_session, mock_preset, configure_db_mock):
        # Arrange
        repo = PresetRepository(db_session)
        presets = [
            mock_preset,
            Preset(
                id=uuid4(),
                name="Another Preset",
                telescope_id=mock_preset.telescope_id,
                processing_params={
                    "version": "1.0",
                    "steps": []
                }
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=presets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_telescope(mock_preset.telescope_id)
        
        # Assert
        assert len(result) == 2
        assert all(p.telescope_id == mock_preset.telescope_id for p in result)

    async def test_get_by_object_type(self, db_session, mock_preset, configure_db_mock):
        # Arrange
        repo = PresetRepository(db_session)
        object_type = "nebula"
        presets = [
            mock_preset,
            Preset(
                id=uuid4(),
                name="Another Preset",
                telescope_id=str(uuid4()),
                target_type=object_type,
                processing_params={
                    "version": "1.0",
                    "steps": []
                }
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=presets)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_object_type(object_type)
        
        # Assert
        assert len(result) == 2
        assert all(p.target_type == object_type for p in result)

    async def test_get_usage_stats(self, db_session, mock_preset, configure_db_mock):
        # Arrange
        repo = PresetRepository(db_session)
        stats = {
            "total_uses": 42,
            "average_stretch": 1.5
        }
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.first = MagicMock(return_value=type(
            'StatsResult', 
            (), 
            {'total_uses': stats['total_uses'], 'avg_stretch': stats['average_stretch']}
        )())
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_usage_stats(mock_preset.id)
        
        # Assert
        assert result["total_uses"] == stats["total_uses"]
        assert result["average_stretch"] == stats["average_stretch"]
