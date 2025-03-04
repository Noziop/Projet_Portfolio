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
            # Mise à jour du statut de la tâche
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await self.task_repository.update(task)

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

    async def generate_target_preview(self, target_id: UUID) -> Optional[str]:
        """Génère une preview pour une cible"""
        target = await self.target_repository.get(target_id)
        if not target:
            return None

        files = await self.target_file_repository.get_by_target(target_id)
        if not files:
            return None

        # Utilise le premier fichier disponible pour la preview
        first_file = next((f for f in files if f.in_minio), None)
        if not first_file:
            return None

        try:
            # Génère la preview
            preview_data = await self.storage_service.get_fits_file(first_file.file_path)
            if not preview_data:
                return None

            # Sauvegarde la preview
            preview_path = f"previews/{target_id}/main.png"
            if await self.storage_service.store_preview(preview_data["data"], preview_path):
                return preview_path
            return None
        except Exception as e:
            target_operations.labels(operation='generate_preview', status='failed').inc()
            return None

    async def add_file_from_mast(
        self,
        target_id: UUID,
        file_path: str,
        mast_id: str,
        file_size: int,
        telescope_id: UUID
    ) -> Optional[TargetFile]:
        """Ajoute un fichier téléchargé depuis MAST à un target
        
        Args:
            target_id: ID de la cible
            file_path: Chemin du fichier téléchargé dans MinIO
            mast_id: Identifiant MAST du fichier
            file_size: Taille du fichier en octets
            telescope_id: ID du télescope utilisé
            
        Returns:
            Le fichier créé ou None en cas d'erreur
        """
        try:
            # Récupération de la cible
            target = await self.target_repository.get(target_id)
            if not target:
                logging.error(f"Cible non trouvée: {target_id}")
                return None
                
            # Récupération des filtres pour ce télescope
            filters = await self.filter_repository.get_by_telescope(telescope_id)
            if not filters:
                logging.warning(f"Aucun filtre trouvé pour le télescope {telescope_id}")
            
            # Le fichier est déjà stocké dans MinIO, pas besoin de le stocker à nouveau
            # Création du TargetFile directement avec le chemin MinIO fourni
            target_file = TargetFile(
                target_id=target_id,
                file_path=file_path,  # Utiliser directement le chemin MinIO
                mast_id=mast_id,
                file_size=file_size,
                telescope_id=telescope_id
            )
            
            # Enregistrement dans la base de données
            created_file = await self.target_file_repository.create(target_file)
            
            if created_file:
                logging.info(f"Fichier ajouté avec succès: {file_path}")
                
                # Mise à jour des presets disponibles en fonction du type d'objet
                presets = await self.preset_repository.get_by_object_type(target.object_type)
                for preset in presets:
                    await self.update_preset_availability(target_id, preset.id)
                
                return created_file
            else:
                logging.error("Échec de la création du fichier dans la base de données")
                return None
                
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du fichier MAST: {str(e)}")
            return None
