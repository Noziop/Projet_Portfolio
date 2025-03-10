# app/tasks/download/select.py
import logging
import traceback
import numpy as np

from astroquery.mast import Observations

from app.db.session import SyncSessionLocal
from app.core.celery import celery_app
from app.tasks.common import update_task_status_sync
from app.domain.value_objects.task_types import TaskStatus

# Configuration du logging
select_logger = logging.getLogger('app.task.download.select')

@celery_app.task(name="app.tasks.download.select_files")
def select_files(search_result):
    """Sélectionne les fichiers à télécharger selon les observations"""
    select_logger.info(f"Sélection des fichiers à télécharger pour la tâche {search_result['task_id']}")
    task_id = search_result["task_id"]
    
    with SyncSessionLocal() as session:
        try:
            # Mise à jour du statut
            update_task_status_sync(task_id, TaskStatus.RUNNING, "Sélection des fichiers à télécharger")
            
            # Récupération des informations
            observations = search_result["observations"]
            
            if not observations or len(observations) == 0:
                error_msg = "Aucune observation disponible"
                select_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Préparation des fichiers à télécharger
            all_files_to_download = []
            
            # Pour chaque observation, sélectionner les fichiers
            for obs in observations:
                try:
                    select_logger.info(f"Récupération des produits pour l'observation {obs['obsid']}")
                    
                    # Obtenir les produits disponibles
                    products = Observations.get_product_list(obs)
                    
                    if not products or len(products) == 0:
                        select_logger.warning(f"Aucun produit disponible pour l'observation {obs['obsid']}")
                        continue
                    
                    select_logger.info(f"{len(products)} produits trouvés pour l'observation {obs['obsid']}")
                    
                    # Utiliser la méthode filter_products pour le filtrage
                    try:
                        # Filtrer pour les produits scientifiques de niveau 3
                        filtered_products = Observations.filter_products(
                            products,
                            productType="SCIENCE",
                            calib_level=3
                        )
                        
                        # Si aucun produit de niveau 3, essayer niveau 2
                        if len(filtered_products) == 0:
                            filtered_products = Observations.filter_products(
                                products,
                                productType="SCIENCE",
                                calib_level=2
                            )
                            
                        # Si toujours aucun produit, prendre tous les produits scientifiques
                        if len(filtered_products) == 0:
                            filtered_products = Observations.filter_products(
                                products,
                                productType="SCIENCE"
                            )
                            
                        if len(filtered_products) > 0:
                            select_logger.info(f"Après filtrage: {len(filtered_products)} produits sélectionnés")
                        else:
                            select_logger.warning(f"Aucun produit scientifique trouvé, utilisation de tous les produits disponibles")
                            filtered_products = products
                            
                    except Exception as e:
                        select_logger.warning(f"Erreur lors du filtrage avancé: {str(e)}, utilisation de la méthode standard")
                        # Fallback sur la méthode manuelle originale
                        filtered_products = products
                        
                        # Filtrer par niveau de calibration si disponible
                        if 'calib_level' in products.columns:
                            try:
                                # Préférer le niveau 3 (complètement calibré)
                                lvl3_mask = products['calib_level'] >= 3
                                lvl3_products = products[lvl3_mask]
                                
                                if len(lvl3_products) > 0:
                                    filtered_products = lvl3_products
                                    select_logger.info(f"Utilisation de {len(lvl3_products)} produits de niveau 3+")
                                else:
                                    # Fallback sur niveau 2
                                    lvl2_mask = products['calib_level'] >= 2
                                    lvl2_products = products[lvl2_mask]
                                    
                                    if len(lvl2_products) > 0:
                                        filtered_products = lvl2_products
                                        select_logger.info(f"Utilisation de {len(lvl2_products)} produits de niveau 2+")
                            except Exception as e:
                                select_logger.error(f"Erreur lors du filtrage par niveau de calibration: {str(e)}")
                    
                    # Limiter le nombre de produits pour éviter un téléchargement excessif
                    if len(filtered_products) > 5:
                        filtered_products = filtered_products[:5]
                        select_logger.info(f"Limitation à 5 produits pour l'observation {obs['obsid']}")
                    
                    # Ajouter les produits à la liste des fichiers à télécharger
                    for product in filtered_products:
                        if 'productFilename' in filtered_products.columns:
                            # Gestion des types NumPy pour sérialisation JSON
                            product_data = {}
                            for col in filtered_products.columns:
                                if col != 'productFilename':
                                    val = product[col]
                                    # Conversion des valeurs spéciales non-sérialisables
                                    if isinstance(val, (np.int64, np.int32)):
                                        val = int(val)
                                    elif isinstance(val, (np.float64, np.float32)):
                                        val = float(val)
                                    elif val is np.ma.masked:
                                        val = None
                                    product_data[col] = val
                                    
                            file_info = {
                                "observation_id": obs['obsid'],
                                "filename": product['productFilename'],
                                "product_data": product_data
                            }
                            all_files_to_download.append(file_info)
                
                except Exception as e:
                    select_logger.error(f"Erreur lors du traitement de l'observation {obs['obsid']}: {str(e)}")
                    select_logger.error(traceback.format_exc())
                    continue
            
            # Vérifier si des fichiers ont été trouvés
            if not all_files_to_download:
                error_msg = "Aucun fichier à télécharger n'a été identifié"
                select_logger.error(error_msg)
                update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
                return {"status": "error", "message": error_msg}
            
            select_logger.info(f"{len(all_files_to_download)} fichiers sélectionnés pour téléchargement")
            
            # Division en chunks pour traitement parallèle
            chunk_size = 3  # Taille ajustable selon besoins
            file_chunks = [
                all_files_to_download[i:i+chunk_size] 
                for i in range(0, len(all_files_to_download), chunk_size)
            ]
            
            # Mise à jour du statut
            update_task_status_sync(
                task_id, 
                TaskStatus.RUNNING, 
                f"{len(all_files_to_download)} fichiers à télécharger en {len(file_chunks)} groupes"
            )
            
            return {
                "task_id": task_id,
                "target_id": search_result["target_id"],
                "telescope_id": search_result["telescope_id"],
                "file_chunks": file_chunks,
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Erreur lors de la sélection des fichiers: {str(e)}"
            select_logger.error(f"{error_msg}\n{traceback.format_exc()}")
            update_task_status_sync(task_id, TaskStatus.FAILED, error_msg)
            return {"status": "error", "message": error_msg}
