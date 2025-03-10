# app/tasks/download/search.py
import logging
import traceback
from uuid import UUID

from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
from astroquery.mast import Observations
import numpy as np

from app.db.session import SyncSessionLocal
from app.core.celery import celery_app
from app.tasks.common import update_task_status_sync
from app.domain.value_objects.task_types import TaskStatus
from app.infrastructure.repositories.telescope_repository import TelescopeRepository

# Configuration du logging
search_logger = logging.getLogger('app.task.download.search')

@celery_app.task(name="app.tasks.download.search_observations")
def search_observations(task_id, target_id, telescope_id):
    """Cherche les observations disponibles pour une cible"""
    search_logger.info(f"Démarrage de la recherche d'observations: task_id={task_id}")
    
    with SyncSessionLocal() as session:
        try:
            # Mise à jour du statut initial
            update_task_status_sync(task_id, TaskStatus.RUNNING, "Recherche des observations")
            
            # Récupération des informations sur la cible et le télescope
            from app.domain.models.target import Target
            from sqlalchemy import select
            stmt = select(Target).where(Target.id == UUID(target_id))
            target = session.execute(stmt).scalar_one_or_none()
            
            if not target:
                error_msg = f"Cible non trouvée: {target_id}"
                search_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Vérifier les coordonnées
            if not target.coordinates_ra or not target.coordinates_dec:
                error_msg = f"Coordonnées manquantes pour la cible {target.name}"
                search_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Récupérer le télescope
            telescope_repo = TelescopeRepository(session)
            telescope = telescope_repo.get_sync(UUID(telescope_id))
            
            if not telescope:
                error_msg = f"Télescope non trouvé: {telescope_id}"
                search_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Conversion des coordonnées
            try:
                ra_angle = Angle(target.coordinates_ra, unit=u.hourangle)
                dec_angle = Angle(target.coordinates_dec, unit=u.deg)
                coords = SkyCoord(ra=ra_angle.deg, dec=dec_angle.deg, unit=u.deg)
            except Exception as e:
                error_msg = f"Erreur de conversion des coordonnées: {str(e)}"
                search_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Recherche dans MAST - avec critères spécifiques selon le télescope
            try:
                search_logger.info(f"Recherche MAST pour {target.name} (RA={ra_angle.deg}, DEC={dec_angle.deg})")
                
                # Stratégie 1: Recherche optimisée avec query_criteria
                if telescope.name.upper() in ['JWST', 'HST']:
                    # Utilisation de query_criteria qui est plus efficace pour filtrer directement
                    observations = Observations.query_criteria(
                        coordinates=coords,
                        radius=0.1 * u.deg,
                        obs_collection=telescope.name.upper(),
                        intentType="science"  # Seulement les observations scientifiques
                    )
                else:
                    # Stratégie 2: Recherche par région puis filtrage
                    observations = Observations.query_region(
                        coordinates=coords,
                        radius=0.1 * u.deg
                    )
                    
                    # Filtrage plus souple pour d'autres télescopes qui pourraient avoir une notation différente
                    telescope_upper = telescope.name.upper()
                    mask = np.array([telescope_upper in str(obs_coll).upper() 
                                    for obs_coll in observations['obs_collection']])
                    if np.any(mask):
                        observations = observations[mask]
                
                if not observations or len(observations) == 0:
                    # Essayer une recherche plus large si aucun résultat
                    search_logger.warning(f"Aucune observation trouvée, tentative avec un rayon plus large")
                    observations = Observations.query_region(
                        coordinates=coords,
                        radius=0.3 * u.deg  # Rayon plus large pour la seconde tentative
                    )
                    
                    if telescope.name.upper() in ['JWST', 'HST']:
                        mask = observations['obs_collection'] == telescope.name.upper()
                        if np.any(mask):
                            observations = observations[mask]
                
                if not observations or len(observations) == 0:
                    error_msg = f"Aucune observation trouvée pour {target.name}"
                    search_logger.warning(error_msg)
                    update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                    return {"status": "error", "message": error_msg}
                
                search_logger.info(f"{len(observations)} observations trouvées pour {target.name}")
                
                # Convertir pour la sérialisation en gérant les types spéciaux
                obs_list = []
                for obs in observations:
                    obs_dict = {}
                    for col in observations.columns:
                        val = obs[col]
                        # Conversion des valeurs spéciales non-sérialisables
                        if isinstance(val, (np.int64, np.int32)):
                            val = int(val)
                        elif isinstance(val, (np.float64, np.float32)):
                            val = float(val)
                        elif val is np.ma.masked:
                            val = None
                        obs_dict[col] = val
                    obs_list.append(obs_dict)
                
                update_task_status_sync(task_id, TaskStatus.RUNNING, f"{len(observations)} observations trouvées")
                
                return {
                    "task_id": task_id,
                    "target_id": target_id,
                    "telescope_id": telescope_id,
                    "observations": obs_list,
                    "status": "success"
                }
                
            except Exception as e:
                error_msg = f"Erreur lors de la recherche MAST: {str(e)}"
                search_logger.error(f"{error_msg}\n{traceback.format_exc()}")
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
                
        except Exception as e:
            error_msg = f"Erreur lors de la recherche des observations: {str(e)}"
            search_logger.error(f"{error_msg}\n{traceback.format_exc()}")
            update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
