from typing import Dict, Any, List
from app.db.session import SessionLocal
from app.core.celery import celery_app
import logging
from astroquery.mast import Observations
from ..storage import storage_service
from app.infrastructure.repositories.models.target import Target

class TaskService:
    @celery_app.task(name='download_fits')
    def download_fits(object_name: str, telescope: str) -> Dict[str, Any]:
        """Télécharge les fichiers FITS et les stocke via le storage service"""
        try:
            # Mise à jour du statut initial
            current_task = celery_app.current_task
            current_task.update_state(
                state='PROGRESS',
                meta={'status': f'Recherche des observations pour {object_name}...'}
            )

            # Mise à jour du statut initial
            current_task = celery_app.current_task
            current_task.update_state(
                state='PROGRESS',
                meta={'status': f'Recherche des observations pour {real_name}...'}
            )

            # 1. Recherche des observations
            obs_table = Observations.query_object(real_name, radius=".02 deg")
            
            # 2. Filtrage par télescope
            obs_filtered = obs_table[obs_table['obs_collection'] == telescope]
            if len(obs_filtered) == 0:
                return {
                    'status': 'error',
                    'message': f"Aucune observation {telescope} trouvée pour {real_name}"
                }

            # 3. Obtention des produits
            current_task.update_state(
                state='PROGRESS',
                meta={'status': 'Récupération des produits...'}
            )
            products = Observations.get_product_list(obs_filtered[0])

            # 4. Filtrage des produits FITS
            filtered_products = Observations.filter_products(
                products,
                productType=["SCIENCE"],
                extension="fits"
            )

            if not filtered_products:
                return {
                    'status': 'error',
                    'message': f"Aucun fichier FITS trouvé pour {real_name} avec {telescope}"
                }

            # 5. Téléchargement et stockage
            current_task.update_state(
                state='PROGRESS',
                meta={'status': 'Téléchargement et stockage des fichiers...'}
            )

            uploaded_files = []
            for product in filtered_products:
                result = Observations.download_file(product['dataURI'])
                if result[0] == 'COMPLETE':
                    filename = product['dataURI'].split('/')[-1]
                    storage_path = f"{telescope}/{real_name}/{filename}"
                    if storage_service.store_fits_file(filename, storage_path):
                        uploaded_files.append(storage_path)

            if not uploaded_files:
                return {
                    'status': 'error',
                    'message': "Échec du téléchargement ou du stockage des fichiers"
                }

            return {
                'status': 'success',
                'message': f"{len(uploaded_files)} fichiers traités avec succès pour {real_name}",
                'files': uploaded_files
            }

        except Exception as e:
            logging.error(f"Erreur lors du téléchargement: {str(e)}")
            return {
                'status': 'error',
                'message': f"Erreur lors du téléchargement: {str(e)}"
            }


    # Autres méthodes de gestion des tâches si nécessaire
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Récupère le statut d'une tâche"""
        task = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None
        }
