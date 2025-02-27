# tests/mocks/minio.py
from unittest.mock import MagicMock

class MinioClientMock(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buckets = {}
        
    def put_object(self, bucket_name, object_name, data, length):
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = {}
        self.buckets[bucket_name][object_name] = data
