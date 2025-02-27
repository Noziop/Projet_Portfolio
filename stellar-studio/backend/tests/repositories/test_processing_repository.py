# tests/repositories/test_processing_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.processing_repository import ProcessingRepository
from app.infrastructure.repositories.models.processing import ProcessingJob
from app.domain.value_objects.processing_types import ProcessingStatus, ProcessingStepType

@pytest.mark.asyncio
class TestProcessingRepository:
    @pytest.fixture
    def mock_processing_job(self):
        return ProcessingJob(
            id=uuid4(),
            user_id=str(uuid4()),
            telescope_id=str(uuid4()),
            workflow_id=str(uuid4()),
            target_id=str(uuid4()),
            preset_id=str(uuid4()),
            task_id=str(uuid4()),
            status=ProcessingStatus.PENDING,
            current_step=ProcessingStepType.CALIBRATION,
            steps=[{"type": "CALIBRATION", "params": {}}],
            intermediate_results={
                "histogram": {"min": 0, "max": 255, "mean": 127},
                "noise_level": 0.05
            }
        )

    async def test_get_by_user(self, db_session, mock_processing_job, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        user_id = uuid4()
        mock_processing_job.user_id = str(user_id)
        jobs = [
            mock_processing_job,
            ProcessingJob(
                id=uuid4(),
                user_id=str(user_id),
                telescope_id=str(uuid4()),
                workflow_id=str(uuid4()),
                target_id=str(uuid4()),
                preset_id=str(uuid4()),
                task_id=str(uuid4()),
                status=ProcessingStatus.COMPLETED,
                steps=[{"type": "CALIBRATION", "params": {}}],
                intermediate_results={}
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=jobs)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_user(user_id)
        
        # Assert
        assert len(result) == 2
        assert all(job.user_id == str(user_id) for job in result)

    async def test_get_by_user_with_status(self, db_session, mock_processing_job, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        user_id = uuid4()
        status = ProcessingStatus.PENDING
        mock_processing_job.user_id = str(user_id)
        mock_processing_job.status = status
        jobs = [mock_processing_job]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=jobs)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_user(user_id, status)
        
        # Assert
        assert len(result) == 1
        assert result[0].user_id == str(user_id)
        assert result[0].status == status

    async def test_get_by_target(self, db_session, mock_processing_job, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        target_id = uuid4()
        mock_processing_job.target_id = str(target_id)
        jobs = [
            mock_processing_job,
            ProcessingJob(
                id=uuid4(),
                user_id=str(uuid4()),
                telescope_id=str(uuid4()),
                workflow_id=str(uuid4()),
                target_id=str(target_id),
                preset_id=str(uuid4()),
                task_id=str(uuid4()),
                status=ProcessingStatus.FAILED,
                steps=[{"type": "CALIBRATION", "params": {}}],
                intermediate_results={}
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=jobs)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_target(target_id)
        
        # Assert
        assert len(result) == 2
        assert all(job.target_id == str(target_id) for job in result)

    async def test_update_intermediate_results(self, db_session, mock_processing_job, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        job_id = mock_processing_job.id
        new_results = {
            "histogram": {"min": 10, "max": 240, "mean": 130},
            "noise_level": 0.03,
            "stars_detected": 1250
        }
        
        # Configure mock - Corriger pour utiliser self.get() correctement
        repo.get = AsyncMock(return_value=mock_processing_job)
        
        # Act
        success = await repo.update_intermediate_results(job_id, new_results)
        
        # Assert
        assert success is True
        assert mock_processing_job.intermediate_results == new_results
        db_session.commit.assert_called_once()

    async def test_update_intermediate_results_not_found(self, db_session, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        job_id = uuid4()
        new_results = {"test": "data"}
        
        # Configure mock - Corriger pour utiliser self.get() correctement
        repo.get = AsyncMock(return_value=None)
        
        # Act
        success = await repo.update_intermediate_results(job_id, new_results)
        
        # Assert
        assert success is False
        db_session.commit.assert_not_called()

    async def test_get_job_stats(self, db_session, mock_processing_job, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        job_id = mock_processing_job.id
        
        # Configure mock
        repo.get = AsyncMock(return_value=mock_processing_job)
        
        # Modifier cette partie pour refléter les champs réels utilisés dans la requête
        # Comme 'progress' n'existe pas, nous devons adapter le test
        mock_result = AsyncMock()
        # Créer un objet qui correspond à ce que la requête SQL retournerait
        mock_stats = type('StatsResult', (), {'total_steps': 5, 'avg_progress': 60.0})()
        mock_result.first = MagicMock(return_value=mock_stats)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        stats = await repo.get_job_stats(job_id)
        
        # Assert
        assert stats["status"] == mock_processing_job.status
        # Ne pas vérifier progress car il n'existe pas dans le modèle
        assert stats["total_steps"] == 5
        assert stats["average_progress"] == 60.0
        assert stats["intermediate_results"] == mock_processing_job.intermediate_results

    async def test_get_job_stats_not_found(self, db_session, configure_db_mock):
        # Arrange
        repo = ProcessingRepository(db_session)
        job_id = uuid4()
        
        # Configure mock
        repo.get = AsyncMock(return_value=None)
        
        # Act
        stats = await repo.get_job_stats(job_id)
        
        # Assert
        assert stats is None
