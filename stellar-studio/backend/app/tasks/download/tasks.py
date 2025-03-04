from celery import shared_task, chain
from uuid import UUID
import logging
import asyncio
import re
import os
from contextlib import asynccontextmanager
import traceback
import tempfile

from app.db.session import AsyncSessionLocal
from app.core.celery import celery_app
from app.core.ws.manager import ConnectionManager
from app.domain.value_objects.task_types import TaskStatus
from app.domain.models.target import Target
from app.infrastructure.repositories.task_repository import TaskRepository
from app.services.storage.service import StorageService
from app.infrastructure.repositories.telescope_repository import TelescopeRepository
from app.tasks.processing.tasks import generate_channel_previews

from astroquery.mast import Observations
from astropy.table import Table
from astropy.coordinates import SkyCoord, Angle
import astropy.units as u
from typing import List, Dict, Optional
import numpy as np

# Configuration du logging
task_logger = logging.getLogger('app.task.download')
task_logger.setLevel(logging.INFO)

# Singleton pour le WebSocket manager
ws_manager = ConnectionManager()

async def update_task_status(task_id: str, status: TaskStatus, message: str = ""):
    """Met à jour le statut d'une tâche dans la base de données.
    
    Args:
        task_id: L'identifiant de la tâche
        status: Le nouveau statut
        message: Message optionnel d'erreur ou d'information
    """
    async with AsyncSessionLocal() as session:
        try:
            task_repository = TaskRepository(session)
            task = await task_repository.get(UUID(task_id))
            if task:
                task.status = status
                if message:
                    task.error = message
                await task_repository.update(task)
                task_logger.info(f"Statut de la tâche {task_id} mis à jour: {status.value}")
            else:
                task_logger.error(f"Tâche {task_id} non trouvée")
        except Exception as e:
            task_logger.error(f"Erreur lors de la mise à jour du statut de la tâche {task_id}: {str(e)}")

@asynccontextmanager
async def get_services():
    """Context manager pour créer et gérer les services."""
    from app.services.target.service import TargetService
    async with AsyncSessionLocal() as session:
        storage_service = StorageService()
        target_service = TargetService(
            session=session,
            storage_service=storage_service,
            ws_manager=ws_manager
        )
        try:
            yield storage_service, target_service
        finally:
            pass  # La session sera fermée automatiquement

async def search_mast_for_target(target: Target, telescope_id: str, radius: float = 0.1) -> List[Dict]:
    """Recherche des observations MAST pour une cible spécifique
    
    Args:
        target: La cible pour laquelle rechercher des observations
        telescope_id: ID du télescope à utiliser
        radius: Rayon de recherche en degrés (par défaut 0.1)
        
    Returns:
        Liste des observations trouvées
    """
    try:
        task_logger.info(f"Recherche d'observations pour {target.name} (RA={target.coordinates_ra}, DEC={target.coordinates_dec}, Radius={radius}°)")
        
        # Vérification des coordonnées
        if target.coordinates_ra is None or target.coordinates_dec is None:
            task_logger.error("Coordonnées manquantes: RA ou DEC est None")
            return []
            
        task_logger.debug(f"Coordonnées validées: RA={target.coordinates_ra}, DEC={target.coordinates_dec}")
        
        # Récupération des infos du télescope depuis la BD
        task_logger.debug(f"Tentative de récupération du télescope: {telescope_id}")
        async with AsyncSessionLocal() as session:
            telescope_repo = TelescopeRepository(session)
            telescope = await telescope_repo.get(UUID(telescope_id))
            
            if not telescope:
                task_logger.error(f"Télescope non trouvé: {telescope_id}")
                return []
                
            task_logger.info(f"Télescope trouvé: {telescope.name} (ID: {telescope.id})")
                
            # Conversion des coordonnées de la cible en SkyCoord
            task_logger.debug("Conversion des coordonnées en SkyCoord")
            try:
                # Conversion du format HH:MM:SS.sss en degrés décimaux
                ra_angle = Angle(target.coordinates_ra, unit=u.hourangle)
                dec_angle = Angle(target.coordinates_dec, unit=u.deg)
                
                ra_deg = ra_angle.deg
                dec_deg = dec_angle.deg
                
                task_logger.debug(f"Coordonnées converties: RA={ra_deg}°, DEC={dec_deg}°")
                
                coords = SkyCoord(ra=ra_deg, dec=dec_deg, unit=u.deg)
                task_logger.debug(f"SkyCoord créé: {coords}")
            except Exception as e:
                task_logger.error(f"Erreur lors de la création de SkyCoord: {str(e)}")
                task_logger.error(f"Valeurs utilisées: RA={target.coordinates_ra} ({type(target.coordinates_ra)}), DEC={target.coordinates_dec} ({type(target.coordinates_dec)})")
                task_logger.error(f"Traceback: {traceback.format_exc()}")
                return []
            
            # Configuration des critères de recherche selon le télescope
            task_logger.debug(f"Recherche de région avec rayon: {radius} degrés")
            
            # Exécution de la recherche par région
            try:
                # Utiliser query_region au lieu de query_criteria
                observations = Observations.query_region(
                    coordinates=coords,
                    radius=radius * u.deg
                )
                task_logger.debug("Requête MAST query_region exécutée avec succès")
                
                # Filtrage des résultats selon les critères supplémentaires
                if telescope.name.upper() == 'JWST':
                    observations = observations[observations['obs_collection'] == 'JWST']
                    observations = observations[observations['dataproduct_type'] == 'image']
                    observations = observations[observations['calib_level'] >= 3]
                elif telescope.name.upper() == 'HST':
                    observations = observations[observations['obs_collection'] == 'HST']
                    observations = observations[observations['dataproduct_type'] == 'image']
                    observations = observations[observations['calib_level'] >= 3]
                
                task_logger.debug(f"Après filtrage: {len(observations) if observations else 0} observations")
            except Exception as e:
                task_logger.error(f"Erreur lors de la requête MAST: {str(e)}")
                task_logger.error(f"Traceback: {traceback.format_exc()}")
                return []
            
            if observations is None or len(observations) == 0:
                task_logger.warning(f"Aucune observation trouvée pour {target.name}")
                return []
                
            task_logger.info(f"{len(observations)} observations trouvées pour {target.name}")
            task_logger.debug(f"Premier résultat: {observations[0] if len(observations) > 0 else 'Aucun'}")
            return observations
            
    except Exception as e:
        task_logger.error(f"Erreur lors de la recherche MAST: {str(e)}")
        task_logger.error(f"Traceback: {traceback.format_exc()}")
        return []

@celery_app.task(name="app.tasks.download.tasks.download_mast_files")
def download_mast_files(task_id: str, target_id: str, telescope_id: str):
    """Tâche Celery qui télécharge les fichiers FITS depuis MAST
    
    Args:
        task_id: ID de la tâche en cours
        target_id: ID de la cible
        telescope_id: ID du télescope à utiliser
        
    Returns:
        Un dictionnaire avec les informations de la tâche
    """
    task_logger.info(f"Démarrage du téléchargement MAST: task_id={task_id}, target_id={target_id}, telescope_id={telescope_id}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(
            _download_mast_files_async(task_id, target_id, telescope_id, loop)
        )
        task_logger.info(f"Téléchargement MAST terminé: task_id={task_id}, fichiers téléchargés={len(results.get('files', []))}")
        return results
    except Exception as e:
        task_logger.error(f"Erreur lors du téléchargement MAST: task_id={task_id}, erreur={str(e)}")
        loop.run_until_complete(update_task_status(task_id, TaskStatus.FAILED, str(e)))
        raise
    finally:
        loop.close()

async def _download_mast_files_async(task_id: str, target_id: str, telescope_id: str, loop):
    """Télécharge les fichiers FITS depuis MAST de manière asynchrone
    
    Args:
        task_id: ID de la tâche en cours
        target_id: ID de la cible
        telescope_id: ID du télescope à utiliser
        loop: Loop asyncio à utiliser
        
    Returns:
        Un dictionnaire avec les informations de la tâche
    """
    from app.services.target.service import TargetService
    
    task_logger.info(f"Démarrage de _download_mast_files_async: task_id={task_id}, target_id={target_id}, telescope_id={telescope_id}")
    
    try:
        async with AsyncSessionLocal() as session:
            task_logger.info("Création des services")
            storage_service = StorageService()
            task_logger.info("StorageService créé")
            target_service = TargetService(
                session=session,
                storage_service=storage_service,
                ws_manager=ws_manager
            )
            task_logger.info("TargetService créé")
            task_repository = TaskRepository(session=session)
            task_logger.info("TaskRepository créé")
            
            try:
                # Récupération de la tâche et mise à jour du statut
                task_logger.info(f"Récupération de la tâche: {task_id}")
                task = await task_repository.get(UUID(task_id))
                if not task:
                    task_logger.error(f"Tâche non trouvée: task_id={task_id}")
                    return {"task_id": task_id, "status": "FAILED", "message": "Tâche non trouvée"}
                
                # Mise à jour du statut de la tâche
                task.status = TaskStatus.RUNNING
                task.error = "Recherche d'observations MAST"
                await task_repository.update(task)
                
                # Récupération de l'objet target
                task_logger.info(f"Récupération de la cible: {target_id}")
                target = await target_service.target_repository.get(UUID(target_id))
                if not target:
                    task_logger.error(f"Cible introuvable: {target_id}")
                    task.status = TaskStatus.FAILED
                    task.error = f"Cible introuvable: {target_id}"
                    await task_repository.update(task)
                    return {"task_id": task_id, "status": "FAILED", "message": f"Target not found: {target_id}"}

                # Récupération du télescope
                task_logger.info(f"Récupération du télescope: {telescope_id}")
                try:
                    telescope_repository = TelescopeRepository(session)
                    telescope = await telescope_repository.get(UUID(telescope_id))
                    if not telescope:
                        task_logger.error(f"Télescope introuvable: {telescope_id}")
                        task.status = TaskStatus.FAILED
                        task.error = f"Télescope introuvable: {telescope_id}"
                        await task_repository.update(task)
                        return {"task_id": task_id, "status": "FAILED", "message": f"Telescope not found: {telescope_id}"}
                    task_logger.info(f"Télescope trouvé: {telescope.name}")
                except Exception as e:
                    task_logger.error(f"Erreur lors de la récupération du télescope: {str(e)}")
                    task.status = TaskStatus.FAILED
                    task.error = f"Erreur lors de la récupération du télescope: {str(e)}"
                    await task_repository.update(task)
                    return {"task_id": task_id, "status": "FAILED", "message": str(e)}

                # Recherche des observations MAST
                task_logger.info(f"Recherche des observations MAST pour la cible: {target.name} ({target.coordinates_ra}, {target.coordinates_dec})")
                try:
                    # Vérification des coordonnées
                    if target.coordinates_ra is None or target.coordinates_dec is None:
                        task_logger.error(f"Coordonnées manquantes pour la cible: {target_id}")
                        task.status = TaskStatus.FAILED
                        task.error = f"Coordonnées manquantes pour la cible: {target_id}"
                        await task_repository.update(task)
                        return {"task_id": task_id, "status": "FAILED", "message": f"Missing coordinates for target: {target_id}"}
                    
                    task_logger.info(f"Coordonnées de la cible: RA={target.coordinates_ra}, DEC={target.coordinates_dec}")
                    # Utiliser search_mast_for_target pour trouver les observations
                    observations = await search_mast_for_target(
                        target=target,
                        telescope_id=telescope_id,
                        radius=0.1  # en degrés
                    )
                    task_logger.info(f"Nombre d'observations trouvées: {len(observations) if observations else 0}")
                except Exception as e:
                    task_logger.error(f"Erreur lors de la recherche des observations MAST: {str(e)}")
                    task.status = TaskStatus.FAILED
                    task.error = f"Erreur lors de la recherche des observations MAST: {str(e)}"
                    await task_repository.update(task)
                    return {"task_id": task_id, "status": "FAILED", "message": str(e)}

                # Filtrage et téléchargement des observations
                if not observations or len(observations) == 0:
                    task_logger.warning(f"Aucune observation trouvée pour la cible: {target.name}")
                    task.status = TaskStatus.FAILED
                    task.error = f"Aucune observation trouvée pour la cible: {target.name}"
                    await task_repository.update(task)
                    return {"task_id": task_id, "status": "FAILED", "message": f"No observations found for target: {target.name}"}

                # Téléchargement des fichiers
                downloaded_files = []
                try:
                    task_logger.info(f"Début du téléchargement des fichiers pour {len(observations)} observations")
                    # Filtrer les observations selon le télescope
                    filtered_observations = [
                        obs for obs in observations
                        if telescope.name.lower() in obs["obs_collection"].lower()
                    ]
                    task_logger.info(f"Après filtrage par télescope: {len(filtered_observations)} observations")
                    
                    counter = 0
                    for obs in filtered_observations:
                        try:
                            # Récupération des produits pour cette observation
                            task_logger.info(f"Récupération des produits pour l'observation: {obs['obsid']}")
                            
                            # Ne mettre à jour que si le statut n'est pas déjà RUNNING
                            if task.status != TaskStatus.RUNNING:
                                task.status = TaskStatus.RUNNING
                            
                            # Mettre à jour uniquement le message d'erreur
                            task.error = f"Téléchargement des fichiers ({counter}/{len(filtered_observations)})"
                            await task_repository.update(task)
                            
                            # Récupération des produits
                            products = Observations.get_product_list(obs)
                            task_logger.info(f"Produits trouvés: {len(products)}")
                            
                            # Afficher les informations sur les produits pour le débogage
                            task_logger.info(f"Colonnes disponibles dans les produits: {list(products.columns)}")
                            
                            if len(products) > 0:
                                try:
                                    # Afficher le premier produit pour débogage
                                    first_row = {}
                                    for col in products.columns:
                                        try:
                                            first_row[col] = products[col][0]
                                        except Exception as e:
                                            first_row[col] = f"<Erreur: {str(e)}>"
                                    
                                    task_logger.info(f"Premier produit (exemple): {first_row}")
                                    
                                    # Utiliser numpy.unique pour les colonnes MaskedColumn
                                    # Vérifier les colonnes disponibles
                                    for col_name in ['productType', 'productSubGroupDescription', 'calib_level']:
                                        try:
                                            if col_name in products.columns:
                                                col_values = np.unique(products[col_name]).tolist()
                                                task_logger.info(f"Valeurs uniques pour {col_name}: {col_values}")
                                        except Exception as e:
                                            task_logger.warning(f"Erreur lors de l'extraction des valeurs uniques pour {col_name}: {str(e)}")
                                except Exception as e:
                                    task_logger.error(f"Erreur lors de l'affichage des informations de débogage: {str(e)}")
                            
                            # Test d'un filtre très simple pour voir si nous obtenons des résultats
                            try:
                                # Utiliser des méthodes de filtrage compatibles avec astropy Table
                                calibrated_images = products.copy()
                                
                                # Pour le filtrage, nous allons éviter d'utiliser des méthodes pandas qui pourraient ne pas fonctionner
                                if 'calib_level' in products.columns:
                                    task_logger.info(f"Tentative de filtrage sur calib_level")
                                    # Créer un masque pour les niveaux de calibration ≥ 3
                                    try:
                                        mask_lvl3 = products['calib_level'] >= 3
                                        calibrated_lvl3 = products[mask_lvl3]
                                        task_logger.info(f"Images avec calib_level >= 3: {len(calibrated_lvl3)}")
                                        
                                        if len(calibrated_lvl3) > 0:
                                            calibrated_images = calibrated_lvl3
                                        else:
                                            task_logger.info("Aucune image de niveau 3, essai avec niveau 2")
                                            mask_lvl2 = products['calib_level'] >= 2
                                            calibrated_lvl2 = products[mask_lvl2]
                                            task_logger.info(f"Images avec calib_level >= 2: {len(calibrated_lvl2)}")
                                            
                                            if len(calibrated_lvl2) > 0:
                                                calibrated_images = calibrated_lvl2
                                    except Exception as e:
                                        task_logger.error(f"Erreur lors du filtrage par calib_level: {str(e)}")
                                else:
                                    task_logger.warning("La colonne 'calib_level' n'existe pas dans les données des produits")
                            except Exception as e:
                                task_logger.error(f"Erreur lors du filtrage des produits: {str(e)}")
                                # En cas d'erreur, utiliser tous les produits
                                calibrated_images = products
                            
                            if len(calibrated_images) == 0:
                                task_logger.warning(f"Aucun produit disponible pour l'observation {obs['obsid']}")
                                continue
                                
                            task_logger.info(f"Produits sélectionnés pour téléchargement: {len(calibrated_images)}")
                            
                            # Limiter le nombre de produits pour éviter un téléchargement excessif
                            if len(calibrated_images) > 5:
                                task_logger.info(f"Limitation à 5 produits maximum pour éviter un téléchargement excessif")
                                calibrated_images = calibrated_images[:5]
                            
                            # Créer un répertoire temporaire pour le téléchargement (sous /tmp)
                            download_path = tempfile.mkdtemp()
                            task_logger.info(f"Répertoire temporaire de téléchargement créé: {download_path}")
                            
                            for idx, product_row in enumerate(calibrated_images):
                                try:
                                    # Vérifier si les colonnes nécessaires existent
                                    if 'productFilename' not in calibrated_images.columns:
                                        task_logger.warning(f"La colonne 'productFilename' est manquante dans le produit")
                                        task_logger.info(f"Colonnes disponibles: {list(calibrated_images.columns)}")
                                        continue
                                    
                                    # Obtenir le filename est différent avec astropy Table
                                    try:
                                        filename = product_row['productFilename']
                                        task_logger.info(f"Traitement du produit [{idx+1}/{len(calibrated_images)}]: {filename}")
                                    except Exception as e:
                                        task_logger.error(f"Erreur lors de la récupération du nom de fichier: {str(e)}")
                                        continue
                                    
                                    # Téléchargement du fichier - avec le produit complet, pas juste une ligne
                                    task_logger.info(f"Tentative de téléchargement du fichier: {filename}")
                                    
                                    # Créer un sous-ensemble contenant uniquement cette ligne
                                    single_product = calibrated_images[[idx]]
                                    
                                    try:
                                        manifest = Observations.download_products(
                                            products=single_product,
                                            download_dir=download_path
                                        )
                                        task_logger.info(f"Réponse du téléchargement: {type(manifest).__name__}")
                                        
                                        if manifest is None:
                                            task_logger.warning(f"Le téléchargement a retourné None pour {filename}")
                                            continue
                                            
                                        task_logger.info(f"Manifeste obtenu avec {len(manifest)} entrées")
                                        
                                        if len(manifest) == 0:
                                            task_logger.warning(f"Le téléchargement n'a pas retourné de données pour {filename}")
                                            continue
                                    except Exception as e:
                                        task_logger.error(f"Erreur lors du téléchargement du fichier {filename}: {str(e)}")
                                        continue
                                    
                                    # Vérification du chemin local
                                    expected_path = os.path.join(download_path, filename)
                                    local_path = expected_path
                                    
                                    # Vérifier si le fichier existe au chemin attendu
                                    if not os.path.exists(expected_path):
                                        task_logger.warning(f"Le fichier téléchargé n'existe pas au chemin attendu: {expected_path}")
                                        
                                        # Essayer de trouver le chemin dans le manifeste
                                        try:
                                            if 'Local Path' in manifest.columns:
                                                local_paths = [row['Local Path'] for row in manifest]
                                                task_logger.info(f"Chemins locaux dans le manifeste: {local_paths}")
                                                
                                                # Prendre le premier chemin valide
                                                for path in local_paths:
                                                    if path and os.path.exists(path):
                                                        local_path = path
                                                        task_logger.info(f"Fichier trouvé au chemin: {local_path}")
                                                        break
                                        except Exception as e:
                                            task_logger.error(f"Erreur lors de la recherche du chemin dans le manifeste: {str(e)}")
                                    
                                    # Vérification finale
                                    if not os.path.exists(local_path):
                                        task_logger.error(f"Impossible de trouver le fichier téléchargé: {filename}")
                                        continue
                                        
                                    task_logger.info(f"Fichier téléchargé avec succès: {local_path}")
                                    
                                    # Stocker le fichier dans MinIO
                                    task_logger.info(f"Stockage du fichier dans MinIO: {filename}")
                                    object_name = f"{target_id}/{filename}"
                                    
                                    # Utiliser store_fits_file au lieu de save_file
                                    if storage_service.store_fits_file(local_path, object_name):
                                        task_logger.info(f"Fichier stocké avec succès dans MinIO: {object_name}")
                                        
                                        # Enregistrement du fichier dans la base de données
                                        file_size = os.path.getsize(local_path)
                                        mast_id = f"mast:{telescope.name.lower()}/product/{filename}"
                                        
                                        target_file = await target_service.add_file_from_mast(
                                            target_id=UUID(target_id),
                                            file_path=object_name,  # Chemin dans MinIO, pas local
                                            mast_id=mast_id,
                                            file_size=file_size,
                                            telescope_id=UUID(telescope_id)
                                        )
                                        
                                        if target_file:
                                            downloaded_files.append({
                                                'id': str(target_file.id),
                                                'observation_id': obs['obsid'],
                                                'filename': filename,
                                                'file_path': object_name,
                                                'file_size': file_size
                                            })
                                            counter += 1
                                            task_logger.info(f"Fichier ajouté à la base de données: {target_file.id} - {filename} (taille: {file_size} octets)")
                                        else:
                                            task_logger.warning(f"Impossible d'ajouter le fichier à la base de données: {filename}")
                                    else:
                                        task_logger.error(f"Impossible de stocker le fichier dans MinIO: {filename}")
                                    
                                    # Supprimer le fichier local après le transfert dans MinIO
                                    try:
                                        os.remove(local_path)
                                        task_logger.info(f"Fichier local supprimé: {local_path}")
                                    except Exception as e:
                                        task_logger.warning(f"Impossible de supprimer le fichier local {local_path}: {str(e)}")
                                
                                except Exception as e:
                                    task_logger.error(f"Erreur lors du traitement du produit: {str(e)}")
                                    continue
                        
                        except Exception as e:
                            task_logger.error(f"Erreur lors du traitement de l'observation: {str(e)}")
                            continue
                    
                    # Vérification des résultats
                    if len(downloaded_files) == 0:
                        message = "Aucun fichier n'a pu être téléchargé depuis MAST"
                        task_logger.error(message)
                        task.status = TaskStatus.FAILED
                        task.error = message
                        await task_repository.update(task)
                        return {"task_id": task_id, "status": "FAILED", "message": message}
                    
                    # Mise à jour de la tâche avec succès
                    task.status = TaskStatus.COMPLETED
                    task.error = f"{len(downloaded_files)} fichiers téléchargés avec succès"
                    await task_repository.update(task)
                    
                    # Nettoyer le répertoire temporaire à la fin
                    try:
                        import shutil
                        shutil.rmtree(download_path, ignore_errors=True)
                        task_logger.info(f"Répertoire temporaire nettoyé: {download_path}")
                    except Exception as e:
                        task_logger.warning(f"Impossible de nettoyer le répertoire temporaire {download_path}: {str(e)}")
                    
                    return {
                        "task_id": task_id,
                        "status": "COMPLETED",
                        "message": f"{len(downloaded_files)} fichiers téléchargés avec succès",
                        "files": downloaded_files
                    }
                
                except Exception as e:
                    error_message = f"Erreur lors du téléchargement MAST: {str(e)}"
                    task_logger.error(error_message)
                    task.status = TaskStatus.FAILED
                    task.error = error_message
                    await task_repository.update(task)
                    return {"task_id": task_id, "status": "FAILED", "message": error_message}
            
            except Exception as e:
                error_message = f"Erreur lors du téléchargement MAST: {str(e)}"
                task_logger.error(error_message)
                task.status = TaskStatus.FAILED
                task.error = error_message
                await task_repository.update(task)
                return {"task_id": task_id, "status": "FAILED", "message": error_message}
    
    except Exception as e:
        task_logger.error(f"Erreur lors de la récupération des services: {str(e)}")
        task.status = TaskStatus.FAILED
        task.error = str(e)
        await task_repository.update(task)
        return {"task_id": task_id, "status": "FAILED", "message": str(e)}

