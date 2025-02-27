# tests/mocks/redis.py
from unittest.mock import MagicMock

class RedisMock(MagicMock):
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value, ex=None):
        self.data[key] = value
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = {}
