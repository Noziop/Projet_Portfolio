# tests/mocks/db.py
from unittest.mock import AsyncMock, MagicMock

class AsyncSessionMock(MagicMock):
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass

def create_db_session_mock():
    session = AsyncSessionMock()
    
    # Mock des méthodes async
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    
    # Configuration spéciale pour execute
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none = AsyncMock()  # Doit être un AsyncMock
    session.execute = AsyncMock(return_value=execute_result)
    
    # Mock des méthodes sync
    session.add = MagicMock()
    
    return session
