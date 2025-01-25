# app/infrastructure/repositories/observation_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from .base_repository import BaseRepository
from ..repositories.models.observation import Observation as ObservationModel
from app.domain.models.observation import Observation
from app.domain.value_objects.coordinates import Coordinates

class ObservationRepository(BaseRepository[Observation]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    async def get_by_id(self, id: str) -> Optional[Observation]:
        query = select(ObservationModel).where(ObservationModel.id == id)
        result = await self.db_session.execute(query)
        db_observation = result.scalar_one_or_none()
        
        if db_observation is None:
            return None
            
        return Observation(
            id=db_observation.id,
            telescope_id=db_observation.telescope_id,
            target_id=db_observation.target_id,
            coordinates=Coordinates(
                ra=db_observation.coordinates_ra,
                dec=db_observation.coordinates_dec
            ),
            start_time=db_observation.start_time,
            exposure_time=db_observation.exposure_time,
            instrument=db_observation.instrument,
            filters=db_observation.filters,
            fits_files=db_observation.fits_files,
            preview_url=db_observation.preview_url
        )

    async def list_by_telescope(self, telescope_id: str) -> List[Observation]:
        query = select(ObservationModel).where(ObservationModel.telescope_id == telescope_id)
        result = await self.db_session.execute(query)
        db_observations = result.scalars().all()
        
        return [
            Observation(
                id=db_observation.id,
                telescope_id=db_observation.telescope_id,
                target_id=db_observation.target_id,
                coordinates=Coordinates(
                    ra=db_observation.coordinates_ra,
                    dec=db_observation.coordinates_dec
                ),
                start_time=db_observation.start_time,
                exposure_time=db_observation.exposure_time,
                instrument=db_observation.instrument,
                filters=db_observation.filters,
                fits_files=db_observation.fits_files,
                preview_url=db_observation.preview_url
            )
            for db_observation in db_observations
        ]

    async def create(self, observation: Observation) -> Observation:
        db_observation = ObservationModel(
            id=observation.id,
            telescope_id=observation.telescope_id,
            target_id=observation.target_id,
            coordinates_ra=observation.coordinates.ra,
            coordinates_dec=observation.coordinates.dec,
            start_time=observation.start_time,
            exposure_time=observation.exposure_time,
            instrument=observation.instrument,
            filters=observation.filters,
            fits_files=observation.fits_files,
            preview_url=observation.preview_url
        )
        
        self.db_session.add(db_observation)
        await self.db_session.commit()
        await self.db_session.refresh(db_observation)
        
        return observation

    async def update(self, observation: Observation) -> Observation:
        query = select(ObservationModel).where(ObservationModel.id == observation.id)
        result = await self.db_session.execute(query)
        db_observation = result.scalar_one_or_none()
        
        if db_observation is None:
            raise ValueError(f"Observation with id {observation.id} not found")
            
        db_observation.telescope_id = observation.telescope_id
        db_observation.target_id = observation.target_id
        db_observation.coordinates_ra = observation.coordinates.ra
        db_observation.coordinates_dec = observation.coordinates.dec
        db_observation.start_time = observation.start_time
        db_observation.exposure_time = observation.exposure_time
        db_observation.instrument = observation.instrument
        db_observation.filters = observation.filters
        db_observation.fits_files = observation.fits_files
        db_observation.preview_url = observation.preview_url
        
        await self.db_session.commit()
        await self.db_session.refresh(db_observation)
        
        return observation

    async def delete(self, id: str) -> bool:
        query = select(ObservationModel).where(ObservationModel.id == id)
        result = await self.db_session.execute(query)
        db_observation = result.scalar_one_or_none()
        
        if db_observation is None:
            return False
            
        await self.db_session.delete(db_observation)
        await self.db_session.commit()
        
        return True
