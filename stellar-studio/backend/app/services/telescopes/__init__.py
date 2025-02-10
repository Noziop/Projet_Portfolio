# app/services/telescopes/__init__.py
from .service import TelescopeService
from app.db.session import AsyncSessionLocal
from typing import AsyncGenerator

async def get_telescope_service() -> AsyncGenerator[TelescopeService, None]:
    async with AsyncSessionLocal() as session:
        yield TelescopeService(session)
