from typing import Dict, Any, List
from app.core.celery import celery_app
import logging
from astroquery.mast import Observations
from ..storage import storage_service

class TaskService:
    @celery_app.task(name='app.services.task.download_fits')
    def download_fits(self, object_name: str, telescope: str) -> Dict[str, Any]:
        """Télécharge les fichiers FITS et les stocke via le storage service"""
        try:
            # 1. Recherche des observations
            obs_table = Observations.query_object(object_name, radius=".02 deg")
            
            # 2. Filtrage par télescope
            obs_filtered = obs_table[obs_table['obs_collection'] == telescope]
            if len(obs_filtered) == 0:
                return {
                    "status": "error",
                    "message": f"No {telescope} observations found for {object_name}"
                }

            # 3. Obtention des produits
            products = Observations.get_product_list(obs_filtered[0])

            # 4. Filtrage des produits FITS
            filtered_products = Observations.filter_products(
                products,
                productType=["SCIENCE"],
                extension="fits"
            )

            if not filtered_products:
                return {
                    "status": "error",
                    "message": f"No FITS files found for {object_name} with {telescope}"
                }

            # 5. Téléchargement et stockage
            uploaded_files = []
            for product in filtered_products:
                result = Observations.download_file(product['dataURI'])
                if result[0] == 'COMPLETE':
                    filename = product['dataURI'].split('/')[-1]
                    # Utilisation du storage service pour le stockage
                    storage_path = f"{telescope}/{object_name}/{filename}"
                    if storage_service.store_fits_file(filename, storage_path):
                        uploaded_files.append(storage_path)

            return {
                "status": "success",
                "count": len(uploaded_files),
                "files": uploaded_files
            }

        except Exception as e:
            logging.error(f"Error in FITS download task: {str(e)}")
            return {"status": "error", "message": str(e)}

    # Autres méthodes de gestion des tâches si nécessaire
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Récupère le statut d'une tâche"""
        task = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None
        }
