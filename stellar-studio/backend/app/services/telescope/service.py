# app/services/telescope/service.py
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge, Summary
from app.infrastructure.repositories.telescope_repository import TelescopeRepository
from app.infrastructure.repositories.filter_repository import FilterRepository
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.infrastructure.repositories.models.filter import Filter
from app.infrastructure.repositories.models.preset import Preset
from app.domain.value_objects.telescope_types import TelescopeStatus

# Logging
logger = logging.getLogger(__name__)

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
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)  # Ajout de buckets pour latences plus longues
)

active_telescopes = Gauge(
    'active_telescopes_total',
    'Number of currently active telescopes'
)

# Ajout d'un summary pour mesurer les performances de chaque étape
step_timing = Summary(
    'telescope_step_execution_seconds', 
    'Time spent in each step of telescope operations',
    ['method', 'step']
)

class TelescopeService:
    def __init__(self, session: AsyncSession):
        self.telescope_repository = TelescopeRepository(session)
        self.filter_repository = FilterRepository(session)
        self.preset_repository = PresetRepository(session)

    def _format_instruments(self, telescope: SpaceTelescope) -> None:
        """Formate les instruments d'un télescope pour assurer la compatibilité avec le schéma Pydantic"""
        start_time = time.time()
        
        # Si instruments est None, initialiser comme dictionnaire vide
        if telescope.instruments is None:
            telescope.instruments = {}
            step_timing.labels(method='_format_instruments', step='empty_init').observe(time.time() - start_time)
            return
        
        # Skip si déjà au bon format (dictionnaire avec structure correcte)
        if isinstance(telescope.instruments, dict):
            # Vérification rapide de la structure
            if len(telescope.instruments) == 0 or all(
                isinstance(instrument, dict) and 'name' in instrument 
                for instrument in telescope.instruments.values()
            ):
                # Déjà au bon format, rien à faire
                step_timing.labels(method='_format_instruments', step='already_dict').observe(time.time() - start_time)
                return
                
        # Conversion de liste en dictionnaire si nécessaire
        if isinstance(telescope.instruments, list):
            instruments_dict = {}
            for instrument in telescope.instruments:
                if isinstance(instrument, dict) and 'name' in instrument:
                    instruments_dict[instrument['name']] = {
                        'name': instrument['name'],
                        'description': instrument.get('type', ''),
                        'wavelength_range': instrument.get('wavelength_range', None),
                        'resolution': instrument.get('resolution', None)
                    }
            telescope.instruments = instruments_dict
            
        step_timing.labels(method='_format_instruments', step='processing').observe(time.time() - start_time)

    async def get_telescope(self, telescope_id: UUID) -> Optional[SpaceTelescope]:
        """Récupère un télescope par son ID"""
        with telescope_api_latency.labels(operation='get').time():
            start_time = time.time()
            logger.debug(f"Fetching telescope {telescope_id}")
            
            # Étape 1: Récupération du télescope
            step_start = time.time()
            telescope = await self.telescope_repository.get(telescope_id)
            step_timing.labels(method='get_telescope', step='db_fetch').observe(time.time() - step_start)
            
            if telescope:
                # Étape 2: Formattage des instruments
                step_start = time.time()
                self._format_instruments(telescope)
                step_timing.labels(method='get_telescope', step='format_instruments').observe(time.time() - step_start)
                
                telescope_operations.labels(operation='get', status='success').inc()
                logger.debug(f"Telescope {telescope_id} fetched in {time.time() - start_time:.3f}s")
            else:
                telescope_operations.labels(operation='get', status='failed').inc()
                logger.warning(f"Telescope {telescope_id} not found")
                
            return telescope

    async def get_active_telescopes(self) -> List[SpaceTelescope]:
        """Récupère tous les télescopes actifs"""
        start_time = time.time()
        logger.info("Fetching all active telescopes...")
        
        # Étape 1: Récupération des télescopes
        step_start = time.time()
        telescopes = await self.telescope_repository.get_by_status(TelescopeStatus.ONLINE)
        step_timing.labels(method='get_active_telescopes', step='db_fetch').observe(time.time() - step_start)
        logger.info(f"Retrieved {len(telescopes)} active telescopes from DB in {time.time() - step_start:.3f}s")
        
        # Étape 2: Formattage des instruments
        step_start = time.time()
        for telescope in telescopes:
            self._format_instruments(telescope)
        step_timing.labels(method='get_active_telescopes', step='format_instruments').observe(time.time() - step_start)
        logger.info(f"Formatted instruments in {time.time() - step_start:.3f}s")
        
        active_telescopes.set(len(telescopes))
        
        total_time = time.time() - start_time
        logger.info(f"get_active_telescopes completed in {total_time:.3f}s")
        return telescopes
    
    async def get_by_status(self, status: TelescopeStatus) -> List[SpaceTelescope]:
        """Récupère tous les télescopes par statut"""
        start_time = time.time()
        logger.info(f"Fetching telescopes with status {status.value}...")
        
        # Étape 1: Récupération des télescopes avec méthode optimisée
        step_start = time.time()
        telescopes = await self.telescope_repository.get_by_status(status)
        step_time = time.time() - step_start
        step_timing.labels(method='get_by_status', step='db_fetch').observe(step_time)
        logger.info(f"Retrieved {len(telescopes)} telescopes with status {status.value} in {step_time:.3f}s")
        
        if step_time > 5.0:
            logger.warning(f"Base de données très lente! Requête a pris {step_time:.3f}s - vérifiez les indexes de la table")
        
        # Si aucun résultat ou trop lent, considérer du cache in-memory pour cette session
        if len(telescopes) == 0:
            logger.info("No telescopes found, returning empty list")
            return []
        
        # Étape 2: Formattage des instruments (uniquement si nécessaire)
        step_start = time.time()
        for telescope in telescopes:
            self._format_instruments(telescope)
        step_timing.labels(method='get_by_status', step='format_instruments').observe(time.time() - step_start)
        logger.info(f"Formatted instruments in {time.time() - step_start:.3f}s")
        
        total_time = time.time() - start_time
        logger.info(f"get_by_status completed in {total_time:.3f}s")
        return telescopes

    async def get_telescope_filters(self, telescope_id: UUID) -> List[Filter]:
        """Récupère tous les filtres disponibles pour un télescope"""
        with telescope_api_latency.labels(operation='get_filters').time():
            start_time = time.time()
            filters = await self.filter_repository.get_by_telescope(telescope_id)
            logger.info(f"Filtres récupérés depuis la BD en {time.time() - start_time:.3f}s")
            
            telescope_operations.labels(
                operation='filter_ops',
                status='success' if filters else 'failed'
            ).inc()
            
            # Détacher les filtres du télescope pour éviter les références circulaires
            for f in filters:
                # Stocker uniquement l'ID et le nom du télescope, pas l'objet complet
                telescope_name = f.telescope.name if f.telescope else None
                f.telescope_name = telescope_name
                f.telescope = None  # Supprimer la référence circulaire
            
            return filters

    async def get_telescope_presets(self, telescope_id: UUID) -> List[Preset]:
        """Récupère tous les presets disponibles pour un télescope"""
        with telescope_api_latency.labels(operation='get_presets').time():
            start_time = time.time()
            presets = await self.preset_repository.get_by_telescope(telescope_id)
            logger.info(f"Presets récupérés depuis la BD en {time.time() - start_time:.3f}s")
            
            telescope_operations.labels(
                operation='preset_ops',
                status='success' if presets else 'failed'
            ).inc()
            
            # Détacher les presets du télescope pour éviter les références circulaires
            for p in presets:
                # Stocker uniquement le nom du télescope, pas l'objet complet
                telescope_name = p.telescope.name if p.telescope else None
                p.telescope_name = telescope_name
                p.telescope = None  # Supprimer la référence circulaire
            
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
            if old_status != TelescopeStatus.ONLINE and status == TelescopeStatus.ONLINE:
                active_telescopes.inc()
            elif old_status == TelescopeStatus.ONLINE and status != TelescopeStatus.ONLINE:
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
        if not telescope or telescope.status != TelescopeStatus.ONLINE:
            return False

        # Vérifie que le preset appartient au télescope
        preset = await self.preset_repository.get(preset_id)
        if not preset or preset.telescope_id != telescope_id:
            return False

        # Vérifie que tous les filtres appartiennent au télescope
        telescope_filters = await self.get_telescope_filters(telescope_id)
        telescope_filter_ids = {f.id for f in telescope_filters}
        
        return all(filter_id in telescope_filter_ids for filter_id in filter_ids)
