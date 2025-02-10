# app/services/observation/service.py
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.observation_repository import ObservationRepository
from app.domain.models.observation import Observation
from app.domain.value_objects.coordinates import Coordinates
from app.domain.value_objects.observation_types import InstrumentType, FilterType

class ObservationService:
    def __init__(self, session: AsyncSession = Depends(AsyncSessionLocal)):
        self.repository = ObservationRepository(session)

    async def create_observation(
        self,
        telescope_id: str,
        target_id: str,
        coordinates: Dict[str, str],
        start_time: datetime,
        exposure_time: int,
        instrument: InstrumentType,
        filters: List[FilterType],
        fits_files: List[str]
    ) -> Observation:
        observation = Observation(
            id=str(uuid4()),
            telescope_id=telescope_id,
            target_id=target_id,
            coordinates=Coordinates(
                ra=coordinates['ra'],
                dec=coordinates['dec']
            ),
            start_time=start_time,
            exposure_time=exposure_time,
            instrument=instrument,
            filters=filters,
            fits_files=fits_files
        )
        return await self.repository.create(observation)

    async def get_observation(self, observation_id: str) -> Optional[Observation]:
        observation = await self.repository.get_by_id(observation_id)
        if not observation:
            raise HTTPException(status_code=404, detail="Observation non trouvée")
        return observation

    async def list_telescope_observations(self, telescope_id: str) -> List[Observation]:
        return await self.repository.list_by_telescope(telescope_id)

    async def update_observation(
        self,
        observation_id: str,
        telescope_id: Optional[str] = None,
        target_id: Optional[str] = None,
        coordinates: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        exposure_time: Optional[int] = None,
        instrument: Optional[InstrumentType] = None,
        filters: Optional[List[FilterType]] = None,
        preview_url: Optional[str] = None
    ) -> Observation:
        current_observation = await self.get_observation(observation_id)
        if not current_observation:
            raise HTTPException(status_code=404, detail="Observation non trouvée")

        # Mise à jour uniquement des champs fournis
        updated_observation = Observation(
            id=observation_id,
            telescope_id=telescope_id or current_observation.telescope_id,
            target_id=target_id or current_observation.target_id,
            coordinates=Coordinates(**coordinates) if coordinates else current_observation.coordinates,
            start_time=start_time or current_observation.start_time,
            exposure_time=exposure_time or current_observation.exposure_time,
            instrument=instrument or current_observation.instrument,
            filters=filters or current_observation.filters,
            fits_files=current_observation.fits_files,
            preview_url=preview_url if preview_url is not None else current_observation.preview_url
        )

        return await self.repository.update(updated_observation)

    async def delete_observation(self, observation_id: str) -> bool:
        deleted = await self.repository.delete(observation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Observation non trouvée")
        return True

