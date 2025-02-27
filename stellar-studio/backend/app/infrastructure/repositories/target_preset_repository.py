# app/infrastructure/repositories/target_preset_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.target_preset import TargetPreset

class TargetPresetRepository(BaseRepository[TargetPreset]):
    def __init__(self, session: AsyncSession):
        super().__init__(TargetPreset, session)

    async def get_by_target(self, target_id: UUID) -> List[TargetPreset]:
        """Récupère les presets disponibles pour une cible"""
        query = select(TargetPreset).where(
            TargetPreset.target_id == str(target_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_preset(self, preset_id: UUID) -> List[TargetPreset]:
        """Récupère les cibles utilisant un preset"""
        query = select(TargetPreset).where(
            TargetPreset.preset_id == str(preset_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_availability(self, target_id: UUID, preset_id: UUID, is_available: bool) -> bool:
        """Met à jour la disponibilité d'un preset pour une cible"""
        query = select(TargetPreset).where(
            TargetPreset.target_id == str(target_id),
            TargetPreset.preset_id == str(preset_id)
        )
        result = await self.session.execute(query)
        target_preset = result.scalar_one_or_none()
        
        if target_preset:
            target_preset.is_available = is_available
            await self.session.commit()
            return True
        return False

    async def check_filters_availability(self, target_id: UUID, preset_id: UUID) -> bool:
        """Vérifie si tous les filtres requis sont disponibles pour un preset"""
        from app.infrastructure.repositories.models.preset_filter import PresetFilter
        from app.infrastructure.repositories.models.target_file import TargetFile
        
        # Requête pour trouver les filtres requis qui ne sont pas disponibles
        query = select(PresetFilter.filter_id).where(
            PresetFilter.preset_id == str(preset_id),
            ~PresetFilter.filter_id.in_(
                select(TargetFile.filter_id).where(
                    TargetFile.target_id == str(target_id)
                ).distinct()
            )
        )
        
        result = await self.session.execute(query)
        missing_filters = result.scalars().all()
        
        # Si aucun filtre manquant, alors tous les filtres requis sont disponibles
        return len(missing_filters) == 0

    async def get_recommended_presets(self, target_id: UUID, limit: int = 3) -> List[TargetPreset]:
        """Récupère les presets recommandés pour une cible basés sur la compatibilité"""
        # D'abord récupérer tous les presets disponibles
        available_presets = await self.get_by_target(target_id)
        
        # Vérifier la compatibilité de chaque preset
        compatible_presets = []
        for preset in available_presets:
            if preset.is_available and await self.check_filters_availability(target_id, UUID(preset.preset_id)):
                compatible_presets.append(preset)
        
        # Trier par pertinence (ici simplement par ID, mais pourrait être amélioré)
        # et limiter le nombre de résultats
        return compatible_presets[:limit]