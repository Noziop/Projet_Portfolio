from typing import List, Dict, Optional
from app.db.session import SessionLocal
from app.schemas.telescope import TelescopeResponse, TelescopeCreate, TelescopeUpdate
from .repository import TelescopeRepository
from ..observation import observation_service

class TelescopeService:
    def get_telescopes(self) -> List[TelescopeResponse]:
        """Liste tous les télescopes disponibles"""
        with SessionLocal() as db:
            repository = TelescopeRepository(db)
            telescopes = repository.get_all()
            return [TelescopeResponse.from_orm(t) for t in telescopes]

    def get_telescope(self, telescope_id: str) -> Optional[TelescopeResponse]:
        """Récupère les détails d'un télescope"""
        with SessionLocal() as db:
            repository = TelescopeRepository(db)
            telescope = repository.get_by_id(telescope_id)
            return TelescopeResponse.from_orm(telescope) if telescope else None

    async def get_telescope_observations(self, telescope_id: str, target_name: str):
        """Récupère les observations d'un télescope pour une cible donnée"""
        return await observation_service.get_telescope_observations(telescope_id, target_name)

    # Méthodes CRUD pour l'admin
    def create_telescope(self, telescope_data: TelescopeCreate) -> TelescopeResponse:
        """Crée un nouveau télescope (admin only)"""
        with SessionLocal() as db:
            repository = TelescopeRepository(db)
            telescope = repository.create(telescope_data.model_dump())
            return TelescopeResponse.from_orm(telescope)

    def update_telescope(self, telescope_id: str, telescope_data: TelescopeUpdate) -> Optional[TelescopeResponse]:
        """Met à jour un télescope existant (admin only)"""
        with SessionLocal() as db:
            repository = TelescopeRepository(db)
            telescope = repository.update(telescope_id, telescope_data.model_dump(exclude_unset=True))
            return TelescopeResponse.from_orm(telescope) if telescope else None

    def delete_telescope(self, telescope_id: str) -> bool:
        """Supprime un télescope (admin only)"""
        with SessionLocal() as db:
            repository = TelescopeRepository(db)
            return repository.delete(telescope_id)