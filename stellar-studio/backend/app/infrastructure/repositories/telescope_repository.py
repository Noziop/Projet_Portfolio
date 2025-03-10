# app/infrastructure/repositories/telescope_repository.py
from typing import Optional, List
import time
import logging
import json
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, noload, lazyload, defer
from app.infrastructure.repositories.base_repository import BaseRepository
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.domain.value_objects.telescope_types import TelescopeStatus

# Logging
logger = logging.getLogger(__name__)

class TelescopeRepository(BaseRepository[SpaceTelescope]):
    def __init__(self, session: AsyncSession):
        super().__init__(SpaceTelescope, session)
        
    async def _get_telescope_ids_by_status(self, status: TelescopeStatus) -> List[str]:
        """Récupère uniquement les IDs des télescopes par statut (très rapide)"""
        start_time = time.time()
        
        # Requête SQL brute optimisée pour récupérer uniquement les IDs
        query = text("""
            SELECT id 
            FROM spacetelescopes 
            WHERE status = :status
            LIMIT 100
        """)
        
        result = await self.session.execute(query, {"status": status.value})
        ids = [row[0] for row in result.fetchall()]
        
        logger.debug(f"DB: Retrieved {len(ids)} telescope IDs in {time.time() - start_time:.3f}s")
        return ids

    async def get_by_status_optimized(self, status: TelescopeStatus) -> List[dict]:
        """Version ultra-optimisée avec SQL brut pour contourner l'ORM"""
        start_time = time.time()
        logger.debug(f"DB: Executing optimized get_by_status query for status={status.value}")
        
        # Requête SQL brute pour minimiser le temps de traitement ORM
        # Inclure TOUS les champs nécessaires pour la validation Pydantic
        query = text("""
            SELECT 
                id, name, aperture, focal_length, status, location, 
                instruments, api_endpoint, description,
                created_at, updated_at
            FROM spacetelescopes 
            WHERE status = :status
            LIMIT 100
        """)
        
        try:
            result = await self.session.execute(query, {"status": status.value})
            raw_telescopes = []
            
            # Conversion manuelle en dictionnaires (beaucoup plus rapide que l'ORM)
            for row in result.fetchall():
                # Construire un dictionnaire avec toutes les données requises par le schéma
                telescope_dict = {
                    "id": row[0],
                    "name": row[1],
                    "aperture": row[2],
                    "focal_length": row[3], 
                    "status": row[4].lower() if row[4] else None,  # Convertir en minuscules pour Pydantic
                    "location": row[5],
                    "instruments": json.loads(row[6]) if row[6] else {},
                    "api_endpoint": row[7],
                    "description": row[8],
                    "created_at": row[9],  # S'assurer que created_at est présent
                    "updated_at": row[10]  # S'assurer que updated_at est présent
                }
                raw_telescopes.append(telescope_dict)
            
            query_time = time.time() - start_time
            logger.debug(f"DB: Retrieved {len(raw_telescopes)} raw telescopes in {query_time:.3f}s")
            
            return raw_telescopes
        
        except Exception as e:
            logger.error(f"DB error in get_by_status_optimized: {str(e)}")
            return []

    async def get_by_status(self, status: TelescopeStatus) -> List[SpaceTelescope]:
        """Récupère tous les télescopes par statut avec chargement extrêmement optimisé"""
        start_time = time.time()
        logger.debug(f"DB: Executing get_by_status query for status={status.value}")
        
        # Essayer d'abord la méthode ultra-optimisée avec SQL brut (contourne l'ORM)
        try:
            raw_telescopes = await self.get_by_status_optimized(status)
            if raw_telescopes:
                # Conversion manuelle en objets SpaceTelescope
                telescopes = []
                for raw in raw_telescopes:
                    telescope = SpaceTelescope()
                    # S'assurer que tous les champs sont correctement définis
                    for key, value in raw.items():
                        setattr(telescope, key, value)
                    # S'assurer que status est un enum et non une chaîne
                    if isinstance(telescope.status, str):
                        telescope.status = TelescopeStatus(telescope.status)
                    telescopes.append(telescope)
                
                query_time = time.time() - start_time
                logger.debug(f"DB: Converted raw data to {len(telescopes)} telescope objects in {query_time:.3f}s")
                return telescopes
        except Exception as e:
            logger.warning(f"Failed to use optimized query: {str(e)}. Falling back to standard ORM.")
        
        # Version fallback: approche en deux étapes avec ORM
        telescope_ids = await self._get_telescope_ids_by_status(status)
        
        if not telescope_ids:
            logger.debug(f"DB: No telescopes found with status={status.value}")
            return []
            
        # Version avec ORM mais optimisée
        query = (
            select(SpaceTelescope)
            .where(SpaceTelescope.id.in_(telescope_ids))
            .options(
                noload('*')  # Désactiver le chargement des relations
            )
        )
        
        try:
            result = await self.session.execute(query)
            telescopes = result.scalars().all()
            
            query_time = time.time() - start_time
            logger.debug(f"DB: Retrieved {len(telescopes)} telescopes in {query_time:.3f}s")
            
            if query_time > 1.0:
                logger.warning(f"Slow query detected: get_by_status took {query_time:.3f}s")
                
            return telescopes
            
        except Exception as e:
            logger.error(f"DB error in get_by_status: {str(e)}")
            # Fallback ultime à la méthode simple
            query = select(SpaceTelescope).where(SpaceTelescope.status == status)
            result = await self.session.execute(query)
            return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[SpaceTelescope]:
        """Récupère un télescope par son nom"""
        start_time = time.time()
        
        query = select(SpaceTelescope).where(SpaceTelescope.name == name)
        result = await self.session.execute(query)
        telescope = result.scalar_one_or_none()
        
        logger.debug(f"DB: get_by_name query executed in {time.time() - start_time:.3f}s")
        return telescope
    
    # Méthodes synchrones pour Celery
    def get_sync(self, telescope_id: str) -> Optional[SpaceTelescope]:
        """Récupère un télescope par son ID (version synchrone)"""
        query = select(SpaceTelescope).where(SpaceTelescope.id == telescope_id)
        result = self.session.execute(query)
        return result.scalar_one_or_none()