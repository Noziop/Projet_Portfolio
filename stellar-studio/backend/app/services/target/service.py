# app/services/target/service.py
from typing import Optional, List, Dict
from uuid import UUID
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram, Gauge
from celery import chain
import logging

from app.core.ws.manager import ConnectionManager
from app.core.ws.events import (
    WebSocketEventType,
    create_download_started_event,
    create_download_progress_event
)

from app.infrastructure.repositories.target_repository import TargetRepository
from app.infrastructure.repositories.target_file_repository import TargetFileRepository
from app.infrastructure.repositories.preset_repository import PresetRepository
from app.infrastructure.repositories.task_repository import TaskRepository
from app.infrastructure.repositories.target_preset_repository import TargetPresetRepository
from app.infrastructure.repositories.filter_repository import FilterRepository

from app.infrastructure.repositories.models.target import Target
from app.infrastructure.repositories.models.target_file import TargetFile
from app.infrastructure.repositories.models.preset import Preset
from app.infrastructure.repositories.models.task import Task
from app.infrastructure.repositories.models.target_preset import TargetPreset

from app.domain.value_objects.target_types import ObjectType, TargetStatus
from app.domain.value_objects.task_types import TaskType, TaskStatus

from app.services.storage.service import StorageService
from app.tasks.processing.tasks import process_hoo_preset, generate_channel_previews, wait_user_validation

# Métriques Prometheus
target_operations = Counter(
    'target_operations_total',
    'Total number of target operations',
    ['operation', 'status']
)

target_processing_duration = Histogram(
    'target_processing_duration_seconds',
    'Time spent processing target operations',
    ['operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

active_downloads = Gauge(
    'active_downloads',
    'Number of active downloads'
)

class TargetService:
    def __init__(
        self, 
        session: AsyncSession,
        storage_service: StorageService,
        ws_manager: ConnectionManager
    ):
        self.target_repository = TargetRepository(session)
        self.target_file_repository = TargetFileRepository(session)
        self.preset_repository = PresetRepository(session)
        self.task_repository = TaskRepository(session)
        self.target_preset_repository = TargetPresetRepository(session)
        self.filter_repository = FilterRepository(session)
        self.storage_service = storage_service
        self.ws_manager = ws_manager

    async def get_target(self, target_id: UUID) -> Optional[Target]:
        """Récupère une cible par son ID"""
        return await self.target_repository.get(target_id)

    async def get_target_with_files(self, target_id: UUID) -> Optional[Dict]:
        """Récupère une cible et ses fichiers associés"""
        target = await self.target_repository.get(target_id)
        if not target:
            return None
        
        files = await self.target_file_repository.get_by_target(target_id)
        return {
            "target": target,
            "files": files
        }

    async def create_target(
        self,
        name: str,
        coordinates_ra: str,
        coordinates_dec: str,
        object_type: ObjectType,
        telescope_id: UUID,
        description: Optional[str] = None
    ) -> Target:
        """Crée une nouvelle cible astronomique"""
        with target_processing_duration.labels(operation='create').time():
            target = Target(
                name=name,
                coordinates_ra=coordinates_ra,
                coordinates_dec=coordinates_dec,
                object_type=object_type,
                telescope_id=telescope_id,
                description=description,
                status=TargetStatus.NEEDS_DOWNLOAD
            )
            created_target = await self.target_repository.create(target)
            target_operations.labels(operation='create', status='success').inc()
            return created_target

    async def start_download(
        self,
        user_id: UUID,
        target_id: UUID,
        preset_id: UUID,
        telescope_id: UUID
    ) -> Optional[Task]:
        """Lance le téléchargement des fichiers depuis MAST pour une cible et un preset.
        """
        from app.tasks.download.tasks import download_mast_files  # Import local pour éviter les imports circulaires
        
        target_processing_duration.labels(operation='download_start').time()
        try:
            target = await self.target_repository.get(target_id)
            preset = await self.preset_repository.get(preset_id)
            
            if not target or not preset:
                await self.ws_manager.send_error(
                    user_id,
                    "Target ou preset invalide"
                )
                return None

            # Si telescope_id n'est pas fourni, utiliser celui associé au target
            if telescope_id is None:
                if target.telescope_id:
                    telescope_id = target.telescope_id
                else:
                    await self.ws_manager.send_error(
                        user_id,
                        "Aucun télescope spécifié ou associé à la cible"
                    )
                    return None

            # Création de la tâche
            task = Task(
                type=TaskType.DOWNLOAD,
                status=TaskStatus.PENDING,
                user_id=user_id,
                params={
                    "target_id": str(target_id),
                    "preset_id": str(preset_id),
                    "telescope_id": str(telescope_id)
                }
            )
            task = await self.task_repository.create(task)

            # Notification WebSocket du démarrage
            await self.ws_manager.send_processing_update(
                user_id,
                create_download_started_event(str(target_id))
            )

            # Chaînage des tâches Celery : téléchargement suivi de la génération des previews
            task_chain = chain(
                download_mast_files.s(
                    str(task.id),
                    str(target_id),
                    str(telescope_id)
                ),
                generate_channel_previews.s()  # Génère une preview pour chaque canal
            )
            task_chain.delay()

            active_downloads.inc()
            target_operations.labels(operation='download_start', status='success').inc()
            return task

        except Exception as e:
            target_operations.labels(operation='download_start', status='failed').inc()
            await self.ws_manager.send_error(
                user_id,
                f"Erreur lors du lancement du téléchargement: {str(e)}"
            )
            return None

    async def update_download_progress(
        self,
        task_id: UUID,
        file_name: str,
        progress: float
    ):
        """Met à jour la progression du téléchargement"""
        task = await self.task_repository.get(task_id)
        if task:
            await self.ws_manager.send_processing_update(
                task.user_id,
                create_download_progress_event(
                    task.params["target_id"],
                    progress,
                    file_name
                )
            )

    async def complete_download(
        self,
        task_id: UUID,
        downloaded_files: List[Dict]
    ) -> bool:
        """Finalise le téléchargement"""
        task = await self.task_repository.get(task_id)
        if not task:
            return False

        try:
            # Mise à jour du statut de la tâche en respectant les transitions valides
            # On ne peut pas passer directement de PENDING à COMPLETED
            if task.status == TaskStatus.PENDING:
                # D'abord passer à RUNNING
                task.status = TaskStatus.RUNNING
                await self.task_repository.update(task)
                # Rafraîchir la tâche avec une nouvelle requête
                task = await self.task_repository.get(task_id)
            
            # Ensuite passage à COMPLETED
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            # Mettre à jour le message avec le nombre de fichiers
            fichiers_txt = f"{len(downloaded_files)} fichiers disponibles"
            task.error = fichiers_txt
            
            await self.task_repository.update(task)

            # Envoi d'une notification WebSocket finale
            try:
                await self.ws_manager.send_processing_update(
                    user_id=task.user_id, 
                    data={
                        "task_id": str(task.id),
                        "progress": 100,
                        "message": f"Téléchargement terminé : {fichiers_txt}",
                        "type": "download_complete",
                        "files": downloaded_files
                    }
                )
            except Exception as e:
                logger.warning(f"Erreur lors de l'envoi de la notification WebSocket de fin: {str(e)}")

            # Mise à jour du statut de la cible
            target_id = UUID(task.params["target_id"])
            await self.update_target_status(
                target_id,
                TargetStatus.READY_FOR_PROCESSING
            )

            active_downloads.dec()
            target_operations.labels(operation='download_complete', status='success').inc()
            return True

        except Exception as e:
            target_operations.labels(operation='download_complete', status='failed').inc()
            await self.ws_manager.send_error(
                task.user_id,
                f"Erreur lors de la finalisation du téléchargement: {str(e)}"
            )
            return False

    async def update_target_status(
        self,
        target_id: UUID,
        status: TargetStatus
    ) -> Optional[Target]:
        """Met à jour le statut d'une cible"""
        with target_processing_duration.labels(operation='update_status').time():
            target = await self.target_repository.get(target_id)
            if not target:
                target_operations.labels(operation='update_status', status='failed').inc()
                return None
            
            target.status = status
            updated_target = await self.target_repository.update(target)
            target_operations.labels(operation='update_status', status='success').inc()
            return updated_target

    async def get_available_presets(self, target_id: UUID) -> List[Dict]:
        """Récupère les presets disponibles pour une cible avec leur statut"""
        target = await self.target_repository.get(target_id)
        if not target:
            return []

        presets = await self.preset_repository.get_by_object_type(target.object_type)
        result = []

        for preset in presets:
            is_available = await self.check_preset_availability(target_id, preset.id)
            
            # Extraire les données de base du preset pour faciliter la sérialisation
            preset_dict = {
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "telescope_id": preset.telescope_id,
                "target_type": preset.target_type,
                "processing_params": preset.processing_params,
                "created_at": preset.created_at,
                "updated_at": preset.updated_at,
                "telescope_name": preset.telescope.name if hasattr(preset, 'telescope') and preset.telescope else None,
                # Inclure des listes vides pour les relations pour respecter le schéma
                "filters": [],
                "preset_filters": []
            }
            
            # Ajouter des informations basiques sur les filtres si disponibles
            if hasattr(preset, 'preset_filters'):
                for pf in preset.preset_filters:
                    if hasattr(pf, 'filter') and pf.filter:
                        # Ajouter les informations complètes sur le filtre (FilterResponse)
                        filter_dict = {
                            "id": pf.filter.id,
                            "name": pf.filter.name,
                            "code": getattr(pf.filter, 'code', None),
                            "wavelength": getattr(pf.filter, 'wavelength', 0),
                            "filter_type": getattr(pf.filter, 'filter_type', None),
                            "description": getattr(pf.filter, 'description', None),
                            "telescope_id": getattr(pf.filter, 'telescope_id', None),
                            "created_at": getattr(pf.filter, 'created_at', None),
                            "updated_at": getattr(pf.filter, 'updated_at', None),
                            "telescope_name": getattr(pf.filter.telescope, 'name', None) if hasattr(pf.filter, 'telescope') else None
                        }
                        preset_dict["filters"].append(filter_dict)
                        
                        # Ajouter les informations sur la relation preset-filtre (PresetFilterResponse)
                        preset_filter_dict = {
                            "id": pf.id if hasattr(pf, 'id') else None,
                            "preset_id": pf.preset_id,
                            "filter_id": pf.filter_id,
                            "order": getattr(pf, 'filter_order', 0),  # Utiliser filter_order ou un ordre par défaut
                            "filter": filter_dict  # Inclure les détails du filtre dans la relation
                        }
                        preset_dict["preset_filters"].append(preset_filter_dict)
            
            result.append({
                "target_id": target_id,
                "preset_id": preset.id,
                "preset": preset_dict,
                "is_available": is_available,
                "required_filters": preset.get_required_filters()
            })

        return result

    async def add_target_file(
        self,
        target_id: UUID,
        filter_id: UUID,
        file_path: str,
        fits_metadata: Dict
    ) -> Optional[TargetFile]:
        """Ajoute un nouveau fichier à une cible"""
        with target_processing_duration.labels(operation='add_file').time():
            # Création de l'objet dans MinIO
            object_name = f"{target_id}/{filter_id}/{os.path.basename(file_path)}"
            if not self.storage_service.store_fits_file(file_path, object_name):
                target_operations.labels(operation='add_file', status='failed').inc()
                return None

            target_file = TargetFile(
                target_id=target_id,
                filter_id=filter_id,
                file_path=object_name,
                file_size=os.path.getsize(file_path),
                in_minio=True,
                fits_metadata=fits_metadata
            )
            
            created_file = await self.target_file_repository.create(target_file)

            # Récupération de la cible
            target = await self.target_repository.get(target_id)
            if not target:
                target_operations.labels(operation='add_file', status='failed').inc()
                return None
            
            # Mise à jour des disponibilités des presets
            presets = await self.preset_repository.get_by_object_type(target.object_type)
            for preset in presets:
                await self.update_preset_availability(target_id, preset.id)
            
            target_operations.labels(operation='add_file', status='success').inc()
            return created_file
        
    async def check_preset_availability(self, target_id: UUID, preset_id: UUID) -> bool:
        """Vérifie si un preset est disponible pour une cible"""
        target_preset = await self.target_preset_repository.get_by_target_and_preset(
            target_id,
            preset_id
        )
        if not target_preset:
            return False
        return target_preset.is_available

    async def update_preset_availability(self, target_id: UUID, preset_id: UUID) -> bool:
        """Met à jour la disponibilité d'un preset pour une cible"""
        target = await self.target_repository.get(target_id)
        preset = await self.preset_repository.get(preset_id)
        if not target or not preset:
            return False

        # Vérifie la disponibilité des filtres requis
        files = await self.target_file_repository.get_by_target(target_id)
        available_filters = {str(f.filter_id) for f in files if f.in_minio}
        required_filters = preset.get_required_filters()

        is_available = all(filter_id in available_filters for filter_id in required_filters)

        # Met à jour la disponibilité
        target_preset = await self.target_preset_repository.get_by_target_and_preset(
            target_id,
            preset_id
        )
        if target_preset:
            target_preset.is_available = is_available
            await self.target_preset_repository.update(target_preset)
        return is_available

    async def generate_target_preview(self, target_id: UUID, preset_id: Optional[int] = None) -> Optional[dict]:
        """
        Génère ou récupère une prévisualisation pour une cible et un preset optionnel.
        
        Args:
            target_id: ID de la cible
            preset_id: ID du preset (optionnel)
            
        Returns:
            Un dictionnaire contenant les URLs des prévisualisations disponibles
        """
        target = await self.target_repository.get(target_id)
        if not target:
            return None
            
        # Si aucun preset n'est spécifié, en choisir un (premier disponible ou défaut)
        if preset_id is None:
            # Récupérer les presets disponibles pour cette cible
            target_presets = await self.target_preset_repository.get_by_target(target_id)
            if target_presets:
                preset_id = target_presets[0].preset_id
            else:
                # Utiliser un preset par défaut (RGB ou le premier disponible)
                from app.infrastructure.repositories.models import Preset
                from sqlalchemy import select
                
                async with self.session.begin():
                    # Essayer de trouver preset RGB
                    stmt = select(Preset).where(Preset.preset_type == "RGB")
                    result = await self.session.execute(stmt)
                    rgb_preset = result.scalars().first()
                    
                    if rgb_preset:
                        preset_id = rgb_preset.id
                    else:
                        # Prendre le premier preset disponible
                        stmt = select(Preset)
                        result = await self.session.execute(stmt)
                        first_preset = result.scalars().first()
                        
                        if first_preset:
                            preset_id = first_preset.id
                        else:
                            return None  # Aucun preset disponible
        
        # Vérifier les fichiers existants pour cette cible et ce preset
        files_info = await self.storage_service.check_files_exist(target_id, preset_id)
        
        # Initialiser le résultat
        result = {
            "preview_urls": {},
            "all_files_available": files_info["exists"]
        }
        
        # S'il y a des JPG disponibles, les utiliser
        if files_info["jpg_files"]:
            for jpg_path in files_info["jpg_files"]:
                # Extraire le nom du filtre du chemin
                filter_name = jpg_path.split("/")[-1].replace(".jpg", "")
                result["preview_urls"][filter_name] = jpg_path
            return result
            
        # S'il y a des FITS disponibles, générer des prévisualisations
        if files_info["fits_files"]:
            for fits_path in files_info["fits_files"]:
                try:
                    # Générer la prévisualisation
                    fits_data = await self.storage_service.get_fits_file(fits_path)
                    if fits_data:
                        # Extraire le nom du filtre du chemin
                        filter_name = fits_path.split("/")[-1].replace(".fits", "")
                        preview_path = f"previews/{target.id}/{filter_name}.png"
                        
                        # Stocker la prévisualisation
                        if await self.storage_service.store_preview(fits_data["data"], preview_path):
                            result["preview_urls"][filter_name] = preview_path
                except Exception as e:
                    logger.exception(f"Erreur lors de la génération de la prévisualisation: {str(e)}")
            
            # Si au moins une prévisualisation a été générée, renvoyer le résultat
            if result["preview_urls"]:
                return result
        
        # Aucune prévisualisation disponible
        return None

    async def add_file_from_mast(
        self,
        target_id: UUID,
        file_path: str,
        mast_id: str,
        file_size: int,
        telescope_id: UUID  # On garde ce paramètre pour compatibilité mais on ne l'utilise pas directement
    ) -> Optional[TargetFile]:
        """Ajoute un fichier téléchargé depuis MAST à un target
        
        Args:
            target_id: ID de la cible
            file_path: Chemin du fichier téléchargé dans MinIO
            mast_id: Identifiant MAST du fichier
            file_size: Taille du fichier en octets
            telescope_id: ID du télescope utilisé (pour compatibilité, non utilisé directement)
            
        Returns:
            Le fichier créé ou None en cas d'erreur
        """
        try:
            # Récupération de la cible
            target = await self.target_repository.get(target_id)
            if not target:
                logging.error(f"Cible non trouvée: {target_id}")
                return None
                
            # Extraction du nom du fichier à partir du chemin
            filename = os.path.basename(file_path)
            
            # Essayer de détecter le filtre à partir du nom de fichier
            filter_id = None
            for filter_name in ['F200W', 'F187N', 'F277W', 'F356W', 'F444W', 'F480M']:
                if filter_name.lower() in filename.lower():
                    # Chercher le filtre correspondant dans la base de données
                    filter = await self.filter_repository.find_by_name(filter_name)
                    if filter:
                        filter_id = filter.id
                        logging.info(f"Filtre détecté: {filter_name} (ID: {filter_id})")
                        break
            
            # Si aucun filtre n'a été trouvé, utiliser un filtre par défaut
            if not filter_id:
                logging.warning(f"Aucun filtre trouvé pour {filename}, utilisation d'un filtre par défaut")
                # Récupérer un filtre par défaut pour ce télescope
                filters = await self.filter_repository.find_by_telescope_id(telescope_id)
                if filters:
                    filter_id = filters[0].id
                    logging.info(f"Filtre par défaut utilisé: {filters[0].name} (ID: {filter_id})")
                else:
                    logging.error(f"Aucun filtre disponible pour le télescope {telescope_id}")
                    return None
            
            # Création du fichier target
            target_file = TargetFile(
                target_id=target_id,
                filter_id=filter_id,
                file_path=file_path,
                file_size=file_size,
                mast_id=mast_id,
                is_downloaded=True,
                in_minio=True
            )
            
            # On ne spécifie plus telescope_id car la colonne a été supprimée
            # telescope_id est désormais obtenu via la relation avec Target
                
            # Extraction des métadonnées FITS si le fichier est disponible
            # ... (code existant pour les métadonnées)
                
            # Sauvegarde dans la base de données
            created_file = await self.target_file_repository.create(target_file)
            
            logging.info(f"Fichier ajouté: {created_file.id} - {file_path}")
            return created_file
                
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du fichier MAST: {str(e)}")
            # Remontée de l'erreur pour traitement par l'appelant
            raise
