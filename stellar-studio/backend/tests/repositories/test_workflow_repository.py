# tests/repositories/test_workflow_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.workflow_repository import WorkflowRepository
from app.infrastructure.repositories.models.workflow import Workflow

@pytest.mark.asyncio
class TestWorkflowRepository:
    @pytest.fixture
    def mock_workflow(self):
        return Workflow(
            id=uuid4(),
            name="Traitement Nébuleuse",
            description="Workflow optimisé pour les nébuleuses",
            steps=[
                {"name": "Calibration", "type": "CALIBRATION", "params": {"dark_frames": 5}},
                {"name": "Stretching", "type": "STRETCHING", "params": {"factor": 1.5}}
            ],
            required_filters=["H-alpha", "OIII"],
            target_type="NEBULA",
            is_default=False,
            estimated_duration=300,
            execution_count=10
        )

    async def test_get_by_target_type(self, db_session, mock_workflow, configure_db_mock):
        # Arrange
        repo = WorkflowRepository(db_session)
        target_type = "NEBULA"
        mock_workflow.target_type = target_type
        workflows = [
            mock_workflow,
            Workflow(
                id=uuid4(),
                name="Traitement Nébuleuse HOO",
                description="Workflow HOO pour nébuleuses",
                steps=[{"name": "Calibration", "type": "CALIBRATION", "params": {}}],
                required_filters=["H-alpha", "OIII"],
                target_type=target_type,
                is_default=True,
                estimated_duration=240,
                execution_count=5
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=workflows)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_target_type(target_type)
        
        # Assert
        assert len(result) == 2
        assert all(workflow.target_type == target_type for workflow in result)

    async def test_get_default(self, db_session, mock_workflow, configure_db_mock):
        # Arrange
        repo = WorkflowRepository(db_session)
        mock_workflow.is_default = True
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_workflow)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_default()
        
        # Assert
        assert result is not None
        assert result.is_default is True

    async def test_increment_execution_count(self, db_session, mock_workflow, configure_db_mock):
        # Arrange
        repo = WorkflowRepository(db_session)
        workflow_id = str(mock_workflow.id)
        initial_count = mock_workflow.execution_count
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_workflow)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        success = await repo.increment_execution_count(workflow_id)
        
        # Assert
        assert success is True
        assert mock_workflow.execution_count == initial_count + 1
        db_session.commit.assert_called_once()

    async def test_update_estimated_duration(self, db_session, mock_workflow, configure_db_mock):
        # Arrange
        repo = WorkflowRepository(db_session)
        workflow_id = str(mock_workflow.id)
        new_duration = 450
        
        # Configure mock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_workflow)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        success = await repo.update_estimated_duration(workflow_id, new_duration)
        
        # Assert
        assert success is True
        assert mock_workflow.estimated_duration == new_duration
        db_session.commit.assert_called_once()

    async def test_get_workflow_stats(self, db_session, mock_workflow, configure_db_mock):
        # Arrange
        repo = WorkflowRepository(db_session)
        workflow_id = str(mock_workflow.id)
        
        # Configure mocks
        repo.get = AsyncMock(return_value=mock_workflow)
        
        mock_result = AsyncMock()
        mock_stats = type('StatsResult', (), {'avg_duration': 320.5})()
        mock_result.first = MagicMock(return_value=mock_stats)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        stats = await repo.get_workflow_stats(workflow_id)
        
        # Assert
        assert stats is not None
        assert stats["total_executions"] == mock_workflow.execution_count
        assert stats["estimated_duration"] == mock_workflow.estimated_duration
        assert stats["average_duration"] == 320.5
