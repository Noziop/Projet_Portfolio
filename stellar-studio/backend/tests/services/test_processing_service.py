import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Service under test (TaskManager, as it handles processing task creation)
from app.services.task_manager import TaskManager

# Models and dependencies
from app.domain.models.task import Task as DomainTask  # Pydantic model for return type
from app.infrastructure.repositories.models.task import Task as DBTaskModel # SQLAlchemy model for DB interaction
from app.db.session import SessionLocal
# from app.core.celery import celery_app # Will be patched

@pytest.fixture
def task_manager():
    """Fixture to create a TaskManager instance (though its methods are static)."""
    return TaskManager()

class TestProcessingTaskCreation: # Renamed to be more specific

    @pytest.mark.asyncio
    @patch('app.services.task_manager.SessionLocal')
    @patch('app.services.task_manager.celery_app.send_task')
    async def test_create_processing_task_success(self, mock_send_task, mock_session_local, task_manager: TaskManager):
        mock_async_result = MagicMock()
        mock_async_result.id = "test-task-id-123"
        mock_send_task.return_value = mock_async_result

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        mock_session_local.return_value = mock_db_session_instance

        user_id = 1
        task_type = "process_fits" # Corresponds to the processing task in app.tasks.processing
        parameters = {"observation_id": 101, "workflow": "standard_workflow"}

        # Call the method
        created_task_domain_model = await task_manager.create_task(user_id, task_type, parameters)

        # Assertions for celery_app.send_task
        mock_send_task.assert_called_once_with(
            f"app.tasks.{task_type}",
            kwargs=parameters
        )

        # Assertions for database interaction
        mock_session_local.assert_called_once() # Check SessionLocal() was called

        # Check that a DBTaskModel instance was created with the right data and added
        # We need to check the arguments to db.add()
        # The actual DBTaskModel is created inside create_task, so we inspect the call to add()
        args, kwargs = mock_db_session_instance.add.call_args
        assert len(args) == 1
        db_task_instance = args[0]

        assert isinstance(db_task_instance, DBTaskModel)
        assert db_task_instance.id == "test-task-id-123"
        assert db_task_instance.user_id == user_id
        assert db_task_instance.type == task_type
        assert db_task_instance.status == "PENDING"
        assert db_task_instance.parameters == parameters
        assert db_task_instance.created_at is not None # Check it's populated
        from unittest.mock import ANY # Local import for ANY
        assert db_task_instance.created_at == ANY # Check it's populated, exact time is tricky

        mock_db_session_instance.commit.assert_called_once()

        # Assertions for the returned domain model
        assert isinstance(created_task_domain_model, DBTaskModel) # The current implementation returns the DB model directly
        assert created_task_domain_model.id == "test-task-id-123"
        assert created_task_domain_model.user_id == user_id
        # ... (add more assertions for other fields of created_task_domain_model if needed)

    @pytest.mark.asyncio
    @patch('app.services.task_manager.SessionLocal')
    @patch('app.services.task_manager.celery_app.send_task')
    async def test_create_task_generic_type(self, mock_send_task, mock_session_local, task_manager: TaskManager):
        # Test with a different task_type to ensure dynamic task naming works
        mock_async_result = MagicMock()
        mock_async_result.id = "test-task-id-456"
        mock_send_task.return_value = mock_async_result

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        mock_session_local.return_value = mock_db_session_instance

        user_id = 2
        task_type = "some_other_task"
        parameters = {"param1": "value1"}

        await task_manager.create_task(user_id, task_type, parameters)

        mock_send_task.assert_called_once_with(
            f"app.tasks.{task_type}", # Checks dynamic task name
            kwargs=parameters
        )

        args, _ = mock_db_session_instance.add.call_args
        db_task_instance = args[0]
        assert db_task_instance.type == task_type # Verify correct type stored
        assert db_task_instance.created_at is not None # Check it's populated

    @pytest.mark.asyncio
    @patch('app.services.task_manager.SessionLocal')
    @patch('app.services.task_manager.celery_app.send_task', side_effect=Exception("Celery error"))
    async def test_create_task_celery_send_exception(self, mock_send_task, mock_session_local, task_manager: TaskManager):
        # Test behavior when celery_app.send_task raises an exception

        mock_db_session_instance = MagicMock()
        mock_db_session_instance.__enter__.return_value = mock_db_session_instance
        mock_session_local.return_value = mock_db_session_instance

        user_id = 3
        task_type = "process_fits"
        parameters = {"observation_id": 202}

        with pytest.raises(Exception, match="Celery error"):
            await task_manager.create_task(user_id, task_type, parameters)

        # Ensure no database commit occurred if Celery fails before DB operations
        mock_session_local.assert_not_called() # SessionLocal() itself might not be called if send_task is first and fails.
                                               # Or if it is, db.add/commit should not be.
                                               # Current code: send_task is first.
        mock_db_session_instance.add.assert_not_called()
        mock_db_session_instance.commit.assert_not_called()

    # Consider a test for DB commit failure if critical, though often harder to mock reliably
    # For example, if db.commit() itself raised an OperationalError.
    # This would require mock_db_session_instance.commit.side_effect = SomeDBException.
    # The current TaskManager doesn't have explicit error handling for db.commit failure.

    # Note: The current TaskManager.create_task returns the SQLAlchemy model instance directly,
    # not a Pydantic domain model (DomainTask). If it were to return a Pydantic model,
    # the assertions on `created_task_domain_model` would need to align with `DomainTask` fields
    # and potentially a `DomainTask.from_orm(db_task_instance)` call or similar.
    # For now, tests assume it returns the DBTaskModel instance based on the code.

    # If app.tasks.processing.process_fits had logic, separate tests for that task
    # would be in a different file, likely tests.tasks.test_processing_tasks.
    # Those tests would mock Minio, Observations, etc., as per the task's internal logic.
    # Since process_fits is currently `pass`, there's nothing to test there yet.
