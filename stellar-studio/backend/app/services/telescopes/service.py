# app/services/telescopes/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.telescope_repository import TelescopeRepository
from app.schemas.telescope import TelescopeCreate, TelescopeUpdate, TelescopeResponse
from app.domain.value_objects.telescope_types import TelescopeStatus

class TelescopeService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.repository = TelescopeRepository(db_session)

    async def get_telescope(self, telescope_id: str) -> TelescopeResponse:
        telescope = await self.repository.get_by_id(telescope_id)
        if not telescope:
            raise ValueError(f"Télescope avec l'id {telescope_id} introuvable")
        return TelescopeResponse.model_validate(telescope)

    async def list_telescopes(self):
        telescopes = await self.repository.list()
        return [TelescopeResponse.model_validate(t) for t in telescopes]

    async def create_telescope(self, telescope_data: TelescopeCreate) -> TelescopeResponse:
        telescope = await self.repository.create(telescope_data.model_dump())
        return TelescopeResponse.model_validate(telescope)

    async def update_telescope(self, telescope_id: str, telescope_data: TelescopeUpdate) -> TelescopeResponse:
        telescope = await self.repository.get_by_id(telescope_id)
        if not telescope:
            raise ValueError(f"Télescope avec l'id {telescope_id} introuvable")
        updated_telescope = await self.repository.update(telescope_data.model_dump(exclude_unset=True))
        return TelescopeResponse.model_validate(updated_telescope)

    async def delete_telescope(self, telescope_id: str) -> bool:
        telescope = await self.repository.get_by_id(telescope_id)
        if not telescope:
            raise ValueError(f"Télescope avec l'id {telescope_id} introuvable")
        return await self.repository.delete(telescope_id)

    async def change_telescope_status(self, telescope_id: str, status: TelescopeStatus) -> TelescopeResponse:
        """Change le statut d'un télescope"""
        telescope = await self.repository.get_by_id(telescope_id)
        if not telescope:
            raise ValueError(f"Télescope avec l'id {telescope_id} introuvable")
        
        update_data = TelescopeUpdate(status=status)
        updated_telescope = await self.repository.update(telescope_id, update_data.model_dump(exclude_unset=True))
        return TelescopeResponse.model_validate(updated_telescope)

    async def activate_telescope(self, telescope_id: str) -> TelescopeResponse:
        """Active un télescope"""
        return await self.change_telescope_status(telescope_id, TelescopeStatus.ACTIVE)

    async def deactivate_telescope(self, telescope_id: str) -> TelescopeResponse:
        """Désactive un télescope"""
        return await self.change_telescope_status(telescope_id, TelescopeStatus.OFFLINE)

    async def set_maintenance_mode(self, telescope_id: str) -> TelescopeResponse:
        """Met un télescope en maintenance"""
        return await self.change_telescope_status(telescope_id, TelescopeStatus.MAINTENANCE)