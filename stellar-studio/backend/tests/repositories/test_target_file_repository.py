# tests/repositories/test_target_file_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.repositories.target_file_repository import TargetFileRepository
from app.infrastructure.repositories.models.target_file import TargetFile

@pytest.mark.asyncio
class TestTargetFileRepository:
    @pytest.fixture
    def mock_target_file(self):
        return TargetFile(
            id=uuid4(),
            target_id=str(uuid4()),
            filter_id=str(uuid4()),
            file_path="data/fits/target1/image.fits",
            file_size=1024000,
            is_downloaded=True,
            in_minio=True,
            fits_metadata={
                "SIMPLE": True,
                "BITPIX": 16,
                "NAXIS": 2,
                "NAXIS1": 1024,
                "NAXIS2": 1024
            }
        )

    async def test_get_by_target(self, db_session, mock_target_file, configure_db_mock):
        # Arrange
        repo = TargetFileRepository(db_session)
        target_id = uuid4()
        mock_target_file.target_id = str(target_id)
        files = [
            mock_target_file,
            TargetFile(
                id=uuid4(),
                target_id=str(target_id),
                filter_id=str(uuid4()),
                file_path="data/fits/target1/image2.fits",
                file_size=2048000,
                is_downloaded=True,
                in_minio=True,
                fits_metadata={
                    "SIMPLE": True,
                    "BITPIX": 16,
                    "NAXIS": 2
                }
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=files)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_target(target_id)
        
        # Assert
        assert len(result) == 2
        assert all(file.target_id == str(target_id) for file in result)

    async def test_get_by_filter(self, db_session, mock_target_file, configure_db_mock):
        # Arrange
        repo = TargetFileRepository(db_session)
        filter_id = uuid4()
        mock_target_file.filter_id = str(filter_id)
        files = [
            mock_target_file,
            TargetFile(
                id=uuid4(),
                target_id=str(uuid4()),
                filter_id=str(filter_id),
                file_path="data/fits/target2/image.fits",
                file_size=3072000,
                is_downloaded=True,
                in_minio=True,
                fits_metadata={
                    "SIMPLE": True,
                    "BITPIX": 16,
                    "NAXIS": 2
                }
            )
        ]
        
        # Configure mock
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all = MagicMock(return_value=files)
        mock_result.scalars = MagicMock(return_value=mock_scalars)
        db_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        result = await repo.get_by_filter(filter_id)
        
        # Assert
        assert len(result) == 2
        assert all(file.filter_id == str(filter_id) for file in result)
