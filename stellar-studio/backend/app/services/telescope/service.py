# app/services/telescope/service.py
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge
from app.infrastructure.repositories.telescope_repository import TelescopeRepository
from app.infrastructure.repositories.filter_repository import FilterRepository
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.infrastructure.repositories.models.filter import Filter
from app.infrastructure.repositories.models.preset import Preset
from app.domain.value_objects.telescope_types import TelescopeStatus

# Métriques Prometheus
telescope_operations = Counter(
    'telescope_operations_total',
    'Total number of telescope operations',
    ['operation', 'status']  # get, update, filter_ops, preset_ops x success/failed
)

telescope_api_latency = Histogram(
    'telescope_api_latency_seconds',
    'Latency of telescope API operations',
    ['operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

active_telescopes = Gauge(
    'active_telescopes_total',
    'Number of currently active telescopes'
)

class TelescopeService:
    def __init__(self, session: AsyncSession):
        self.telescope_repository = TelescopeRepository(session)
        self.filter_repository = FilterRepository(session)
        self.preset_repository = PresetRepository(session)

    async def get_telescope(self, telescope_id: UUID) -> Optional[SpaceTelescope]:
        """Récupère un télescope par son ID"""
        with telescope_api_latency.labels(operation='get').time():
            telescope = await self.telescope_repository.get(telescope_id)
            if telescope:
                telescope_operations.labels(operation='get', status='success').inc()
            else:
                telescope_operations.labels(operation='get', status='failed').inc()
            return telescope

    async def get_active_telescopes(self) -> List[SpaceTelescope]:
        """Récupère tous les télescopes actifs"""
        telescopes = await self.telescope_repository.get_by_status(TelescopeStatus.ACTIVE)
        active_telescopes.set(len(telescopes))
        return telescopes

    async def get_telescope_filters(self, telescope_id: UUID) -> List[Filter]:
        """Récupère tous les filtres disponibles pour un télescope"""
        with telescope_api_latency.labels(operation='get_filters').time():
            filters = await self.filter_repository.get_by_telescope(telescope_id)
            telescope_operations.labels(
                operation='filter_ops',
                status='success' if filters else 'failed'
            ).inc()
            return filters

    async def get_telescope_presets(self, telescope_id: UUID) -> List[Preset]:
        """Récupère tous les presets disponibles pour un télescope"""
        with telescope_api_latency.labels(operation='get_presets').time():
            presets = await self.preset_repository.get_by_telescope(telescope_id)
            telescope_operations.labels(
                operation='preset_ops',
                status='success' if presets else 'failed'
            ).inc()
            return presets

    async def update_telescope_status(
        self,
        telescope_id: UUID,
        status: TelescopeStatus
    ) -> Optional[SpaceTelescope]:
        """Met à jour le statut d'un télescope"""
        with telescope_api_latency.labels(operation='update_status').time():
            telescope = await self.telescope_repository.get(telescope_id)
            if not telescope:
                telescope_operations.labels(operation='update', status='failed').inc()
                return None
            
            old_status = telescope.status
            telescope.status = status
            updated_telescope = await self.telescope_repository.update(telescope)
            
            # Mise à jour du compteur de télescopes actifs
            if old_status != TelescopeStatus.ACTIVE and status == TelescopeStatus.ACTIVE:
                active_telescopes.inc()
            elif old_status == TelescopeStatus.ACTIVE and status != TelescopeStatus.ACTIVE:
                active_telescopes.dec()
            
            telescope_operations.labels(operation='update', status='success').inc()
            return updated_telescope

    async def get_telescope_capabilities(self, telescope_id: UUID) -> Optional[Dict]:
        """Récupère les capacités d'un télescope (filtres + presets)"""
        with telescope_api_latency.labels(operation='get_capabilities').time():
            telescope = await self.telescope_repository.get(telescope_id)
            if not telescope:
                telescope_operations.labels(operation='get', status='failed').inc()
                return None

            filters = await self.get_telescope_filters(telescope_id)
            presets = await self.get_telescope_presets(telescope_id)

            return {
                "telescope": telescope,
                "filters": filters,
                "presets": presets,
                "instruments": telescope.instruments
            }

    async def validate_telescope_configuration(
        self,
        telescope_id: UUID,
        preset_id: UUID,
        filter_ids: List[UUID]
    ) -> bool:
        """Valide qu'une configuration (preset + filtres) est valide pour un télescope"""
        telescope = await self.get_telescope(telescope_id)
        if not telescope or telescope.status != TelescopeStatus.ACTIVE:
            return False

        # Vérifie que le preset appartient au télescope
        preset = await self.preset_repository.get(preset_id)
        if not preset or preset.telescope_id != telescope_id:
            return False

        # Vérifie que tous les filtres appartiennent au télescope
        telescope_filters = await self.get_telescope_filters(telescope_id)
        telescope_filter_ids = {f.id for f in telescope_filters}
        
        return all(filter_id in telescope_filter_ids for filter_id in filter_ids)
