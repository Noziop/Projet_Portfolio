# tests/repositories/test_task_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.task_repository import TaskRepository
from app.infrastructure.repositories.models.task import Task
from app.domain.value_objects.task_types import TaskType, TaskStatus

@pytest.mark.asyncio
class TestTaskRepository:
    @pytest.fixture
    def mock_task(self):
        return Task(
            id=uuid4(),
            type=TaskType.DOWNLOAD,
            status=TaskStatus.PENDING,
            progress=0.0,
            params={"url": "https://example.com/data.fits"},
            user_id=str(uuid4())
        )

    async def test_get_by_user(self, db_session, mock_task, configure_db_mock):
        # Arrange
        repo = TaskRepository(db_session)
        user_id = uuid4()
        mock_task.user_id = str(user_id)
        tasks = [
            mock_task,
            Task(
                id=uuid4(),
                type=TaskType.PROCESSING,
                status=TaskStatus.RUNNING,
                progress=50.0,
                params={"preset": "HOO"},
                user_id=str(user_id)
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=tasks)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_user(user_id)
        
        # Assert
        assert len(result) == 2
        assert all(task.user_id == str(user_id) for task in result)

    async def test_get_by_status(self, db_session, mock_task, configure_db_mock):
        # Arrange
        repo = TaskRepository(db_session)
        status = TaskStatus.PENDING
        mock_task.status = status
        tasks = [
            mock_task,
            Task(
                id=uuid4(),
                type=TaskType.CALIBRATION,
                status=status,
                progress=0.0,
                params={"dark_frames": 5},
                user_id=str(uuid4())
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=tasks)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_status(status)
        
        # Assert
        assert len(result) == 2
        assert all(task.status == status for task in result)

    async def test_get_by_type(self, db_session, mock_task, configure_db_mock):
        # Arrange
        repo = TaskRepository(db_session)
        task_type = TaskType.DOWNLOAD
        mock_task.type = task_type
        tasks = [
            mock_task,
            Task(
                id=uuid4(),
                type=task_type,
                status=TaskStatus.COMPLETED,
                progress=100.0,
                params={"url": "https://example.com/other.fits"},
                user_id=str(uuid4()),
                result={"file_path": "/data/fits/image.fits"}
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=tasks)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_type(task_type)
        
        # Assert
        assert len(result) == 2
        assert all(task.type == task_type for task in result)
