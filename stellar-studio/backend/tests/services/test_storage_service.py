import os
import pytest
from unittest.mock import MagicMock, patch

# --- Pre-emptive Mocks & Patches ---
class MockSettingsGlobal:
    MINIO_URL = "http://localhost:9000"
    MINIO_ACCESS_KEY = "testaccess"
    MINIO_SECRET_KEY = "testsecret"

# Patch Minio at its source ('minio.Minio') BEFORE it's imported by app.services.storage.service
# Patch settings at its source ('app.core.config.settings')
patcher_minio_global = patch('minio.Minio') # Target the original Minio class globally
patcher_settings_global = patch('app.core.config.settings', MockSettingsGlobal())
# os.getenv and os.path.exists are used within StorageService, so patching them in that module's context is fine.
patcher_os_getenv = patch('app.services.storage.service.os.getenv')
patcher_os_path_exists = patch('app.services.storage.service.os.path.exists')

# Start global patchers
mock_minio_class_started = patcher_minio_global.start()
mock_settings_started = patcher_settings_global.start()
mock_os_getenv_started = patcher_os_getenv.start()
mock_os_path_exists_started = patcher_os_path_exists.start()

# Configure the globally mocked Minio class and its instance
# This configures the mock that will be used by app.services.storage.__init__
mock_os_getenv_started.return_value = 'bucket-at-import-time'
_global_minio_client_mock_instance = MagicMock() # Removed spec=True
_global_minio_client_mock_instance.bucket_exists.return_value = True # For the singleton instantiation
mock_minio_class_started.return_value = _global_minio_client_mock_instance

# Now, safe to import the service and S3Error
# When app.services.storage.__init__ runs, it will use the patched minio.Minio and app.core.config.settings
from app.services.storage.service import StorageService
from minio.error import S3Error

# Helper for creating S3Error instances for testing
def create_mock_s3error(message="Mocked S3 Error", code="NoSuchBucket"):
    mock_response = MagicMock()
    mock_response.status = 404 # Example status
    # Ensure all required string arguments for S3Error are non-empty
    resource = "test-resource" if "test-resource" else "default-resource"
    request_id = "test-req-id" if "test-req-id" else "default-req-id"
    host_id = "test-host-id" if "test-host-id" else "default-host-id"

    # Use a real, albeit simple, dict for response if it's accessed like a dict
    # For now, a MagicMock should suffice if only attributes are accessed.
    # If the actual S3Error class tries to read headers or status from it,
    # those attributes would need to be on mock_response.
    return S3Error(
        code=code if code else "UnknownError", # S3Error code cannot be empty
        message=message,
        resource=resource,
        request_id=request_id,
        host_id=host_id,
        response=mock_response
    )

def stop_global_patchers():
    patcher_minio_global.stop()
    patcher_settings_global.stop()
    patcher_os_getenv.stop()
    patcher_os_path_exists.stop()

# Attempt to register a finalizer with pytest, though conftest.py is more robust
@pytest.fixture(scope="session", autouse=True)
def module_patch_lifespan(request):
    request.addfinalizer(stop_global_patchers)


@pytest.fixture(autouse=True)
def reset_global_mocks_before_each_test():
    """Resets global mocks to a clean state before each test function."""
    mock_os_getenv_started.reset_mock()
    mock_os_getenv_started.return_value = 'test-fits-bucket' # Default for most tests

    _global_minio_client_mock_instance.reset_mock()
    _global_minio_client_mock_instance.bucket_exists.return_value = True
    mock_minio_class_started.return_value = _global_minio_client_mock_instance
    mock_minio_class_started.reset_mock()
    mock_minio_class_started.return_value = _global_minio_client_mock_instance

    mock_os_path_exists_started.reset_mock()

@pytest.fixture
def storage_service() -> StorageService:
    return StorageService()

@pytest.fixture
def mock_minio_client() -> MagicMock:
    return _global_minio_client_mock_instance


class TestStorageService:

    def test_init_ensures_bucket_exists_already_there(self, storage_service: StorageService, mock_minio_client: MagicMock):
        # StorageService init called _ensure_bucket_exists.
        # mock_os_getenv was 'test-fits-bucket' from reset_global_mocks_before_each_test.
        # bucket_exists was True from reset_global_mocks_before_each_test.
        # The calls happen during StorageService() in the fixture.
        # We assert based on the state *after* that instantiation.
        # The first call to bucket_exists with 'test-fits-bucket' happened in storage_service fixture.
        assert mock_minio_client.bucket_exists.call_args_list[0][0][0] == 'test-fits-bucket'
        # Check that make_bucket was not called for 'test-fits-bucket'
        # This requires careful check of calls if make_bucket was called for 'bucket-at-import-time'

        # Simpler: check current state or make a specific call within test
        storage_service._ensure_bucket_exists("test-fits-bucket") # Call it again to be sure of context
        # Assert based on this specific call
        mock_minio_client.bucket_exists.assert_called_with("test-fits-bucket")
        # If make_bucket was called, it would be for 'bucket-at-import-time' or 'new-creation-bucket'
        # For this specific check on "test-fits-bucket", make_bucket should not have been called for it.
        # This is tricky due to the singleton. The test should focus on a fresh instance if possible
        # or be very aware of the singleton's initial state.
        # The current `storage_service` fixture creates a NEW instance, so it's fine.

        # Count calls to make_bucket since the last reset for this specific instance's lifecycle.
        # The reset_global_mocks_before_each_test clears call counts on _global_minio_client_mock_instance.
        calls_to_make_bucket = [call for call_args, call_kwargs in mock_minio_client.make_bucket.call_args_list if call_args[0] == "test-fits-bucket"]
        assert not calls_to_make_bucket


    def test_init_ensures_bucket_creates_if_not_there(self, mock_minio_client: MagicMock):
        global mock_os_getenv_started

        mock_os_getenv_started.return_value = 'new-creation-bucket'
        mock_minio_client.reset_mock()
        mock_minio_client.bucket_exists.return_value = False

        StorageService()

        mock_minio_client.bucket_exists.assert_called_once_with('new-creation-bucket')
        mock_minio_client.make_bucket.assert_called_once_with('new-creation-bucket')

    def test_store_fits_file_success(self, storage_service: StorageService, mock_minio_client: MagicMock):
        global mock_os_path_exists_started
        mock_os_path_exists_started.return_value = True
        file_path = "/fake/path/to/image.fits"
        object_name = "image.fits"

        result = storage_service.store_fits_file(file_path, object_name)

        assert result is True
        mock_os_path_exists_started.assert_called_once_with(file_path)
        mock_minio_client.fput_object.assert_called_once_with(
            "test-fits-bucket",
            object_name,
            file_path,
            content_type="application/fits"
        )

    def test_store_fits_file_not_found(self, storage_service: StorageService, mock_minio_client: MagicMock):
        global mock_os_path_exists_started
        mock_os_path_exists_started.return_value = False
        file_path = "/fake/nonexistent/image.fits"
        object_name = "image.fits"

        result = storage_service.store_fits_file(file_path, object_name)

        assert result is False
        mock_os_path_exists_started.assert_called_once_with(file_path)
        mock_minio_client.fput_object.assert_not_called()

    def test_store_fits_file_s3_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        global mock_os_path_exists_started
        mock_os_path_exists_started.return_value = True
        mock_minio_client.fput_object.side_effect = create_mock_s3error(message="S3 fput_object error")
        file_path = "/fake/path/to/image.fits"
        object_name = "image.fits"

        result = storage_service.store_fits_file(file_path, object_name)
        assert result is False

    def test_get_fits_file_success(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        mock_s3_response_object = MagicMock()
        mock_s3_response_object.read.return_value = b"fits_data_bytes"
        mock_s3_response_object.size = 1024
        mock_s3_response_object.content_type = "application/fits"

        mock_minio_client.get_object.return_value = mock_s3_response_object

        file_info = storage_service.get_fits_file(object_name)

        assert file_info is not None
        assert file_info["data"] == b"fits_data_bytes"
        assert file_info["size"] == 1024
        assert file_info["content_type"] == "application/fits"
        mock_minio_client.get_object.assert_called_once_with("test-fits-bucket", object_name)
        mock_s3_response_object.read.assert_called_once()

    def test_get_fits_file_s3_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        mock_minio_client.get_object.side_effect = create_mock_s3error(message="S3 get_object error")

        file_info = storage_service.get_fits_file(object_name)
        assert file_info is None

    def test_delete_fits_file_success(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        result = storage_service.delete_fits_file(object_name)

        assert result is True
        mock_minio_client.remove_object.assert_called_once_with("test-fits-bucket", object_name)

    def test_delete_fits_file_s3_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        mock_minio_client.remove_object.side_effect = create_mock_s3error(message="S3 remove_object error")

        result = storage_service.delete_fits_file(object_name)
        assert result is False

    def test_init_ensure_bucket_fails_propagates_s3error(self, mock_minio_client: MagicMock):
        original_bucket_exists_side_effect = mock_minio_client.bucket_exists.side_effect
        mock_minio_client.reset_mock()
        mock_minio_client.bucket_exists.side_effect = create_mock_s3error(message="Connection Error during bucket check")

        with pytest.raises(S3Error, match="Connection Error during bucket check"):
            StorageService()

        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.make_bucket.assert_not_called()
        mock_minio_client.bucket_exists.side_effect = original_bucket_exists_side_effect


    def test_store_fits_file_unexpected_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        global mock_os_path_exists_started
        mock_os_path_exists_started.return_value = True
        mock_minio_client.fput_object.side_effect = Exception("Unexpected IO Error")
        file_path = "/fake/path/to/image.fits"
        object_name = "image.fits"

        result = storage_service.store_fits_file(file_path, object_name)
        assert result is False

    def test_get_fits_file_unexpected_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        mock_minio_client.get_object.side_effect = Exception("Unexpected Network Error")

        file_info = storage_service.get_fits_file(object_name)
        assert file_info is None

    def test_delete_fits_file_unexpected_error(self, storage_service: StorageService, mock_minio_client: MagicMock):
        object_name = "image.fits"
        mock_minio_client.remove_object.side_effect = Exception("Unexpected Permission Error")

        result = storage_service.delete_fits_file(object_name)
        assert result is False
