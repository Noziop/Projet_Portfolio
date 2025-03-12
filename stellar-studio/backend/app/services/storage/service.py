# app/services/storage/service.py
from typing import Optional, Dict, Any
import os
import logging
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
from prometheus_client import Counter, Histogram, Gauge
from app.core.config import settings

# Métriques Prometheus
storage_operations = Counter(
    'storage_operations_total',
    'Total number of storage operations',
    ['operation', 'status']  # store, retrieve, delete x success/failed
)

storage_operation_duration = Histogram(
    'storage_operation_duration_seconds',
    'Time spent processing storage operations',
    ['operation'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
)

storage_file_size = Histogram(
    'storage_file_size_bytes',
    'Size distribution of stored files',
    buckets=(1e6, 5e6, 10e6, 50e6, 100e6)  # 1MB à 100MB
)

active_connections = Gauge(
    'minio_active_connections',
    'Number of active connections to MinIO'
)

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL.replace('http://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.fits_bucket = os.getenv('MINIO_BUCKET_NAME', 'fits-files')
        self.preview_bucket = os.getenv('MINIO_PREVIEW_BUCKET', 'previews')
        self._ensure_bucket_exists(self.fits_bucket)
        self._ensure_bucket_exists(self.preview_bucket)
        active_connections.inc()  # Incrémente le compteur de connexions

    def __del__(self):
        active_connections.dec()  # Décrémente le compteur de connexions

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logging.info(f"Bucket '{bucket_name}' created")
        except S3Error as e:
            logging.error(f"Error ensuring bucket exists: {str(e)}")
            raise

    def store_fits_file(self, file_path: str, object_name: str, timeout_seconds: int = 180) -> bool:
        """Stocke un fichier FITS dans MinIO avec un timeout
        
        Pour les fichiers volumineux (>100MB), utilise un téléchargement multipart.
        Pour les fichiers plus petits, utilise l'upload direct avec timeout.

        Args:
            file_path: Chemin du fichier local
            object_name: Nom de l'objet dans MinIO
            timeout_seconds: Temps maximum d'attente en secondes (défaut: 3 minutes)
            
        Returns:
            True si le fichier a été stocké avec succès, False sinon
        """
        with storage_operation_duration.labels(operation='store').time():
            try:
                if not os.path.exists(file_path):
                    logging.error(f"File not found: {file_path}")
                    storage_operations.labels(operation='store', status='failed').inc()
                    return False

                # Mesure de la taille du fichier
                file_size = os.path.getsize(file_path)
                storage_file_size.observe(file_size)
                
                # Pour les gros fichiers, utiliser l'upload multipart via la file d'attente
                if file_size > 100 * 1024 * 1024:  # >100MB
                    logging.info(f"Fichier volumineux ({file_size/1024/1024:.2f} MB): {object_name}")
                    return self._enqueue_multipart_upload(file_path, object_name, file_size)
                
                # Pour les fichiers plus petits, utiliser l'upload direct avec timeout
                return self._direct_upload(file_path, object_name, timeout_seconds)
                
            except Exception as e:
                logging.error(f"Error evaluating file for storage {object_name}: {str(e)}")
                storage_operations.labels(operation='store', status='failed').inc()
                return False
                
    def _direct_upload(self, file_path: str, object_name: str, timeout_seconds: int = 180) -> bool:
        """Upload direct pour les fichiers de taille normale avec timeout"""
        try:
            import threading
            import concurrent.futures
            
            def upload_to_minio():
                try:
                    self.client.fput_object(
                        self.fits_bucket,
                        object_name,
                        file_path,
                        content_type="application/fits"
                    )
                    return True
                except Exception as e:
                    logging.error(f"Erreur thread upload: {str(e)}")
                    return False
            
            # Exécuter dans un pool avec timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(upload_to_minio)
                try:
                    success = future.result(timeout=timeout_seconds)
                    if success:
                        logging.info(f"Successfully stored {object_name} in MinIO")
                        storage_operations.labels(operation='store', status='success').inc()
                        return True
                    else:
                        logging.error(f"Échec du stockage de {object_name}")
                        storage_operations.labels(operation='store', status='failed').inc()
                        return False
                except concurrent.futures.TimeoutError:
                    logging.error(f"Timeout après {timeout_seconds}s pour {object_name}")
                    storage_operations.labels(operation='store', status='timeout').inc()
                    return False
        except Exception as e:
            logging.error(f"Error in direct upload for {object_name}: {str(e)}")
            storage_operations.labels(operation='store', status='failed').inc()
            return False
    
    def _enqueue_multipart_upload(self, file_path: str, object_name: str, file_size: int) -> bool:
        """Ajoute le fichier à la file d'attente de téléchargements multipart"""
        try:
            import uuid
            import json
            import redis
            from datetime import datetime
            
            # Créer une connexion Redis synchrone
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_SESSION_DB
            )
            
            # Préparer les informations de transfert
            transfer_info = {
                'file_path': file_path,
                'object_name': object_name,
                'file_size': file_size,
                'part_size': 8 * 1024 * 1024,  # 8MB par partie
                'status': 'pending',
                'timestamp': datetime.now().isoformat(),
                'attempts': 0,
                'uploaded_parts': []
            }
            
            # Ajouter à la file d'attente Redis
            queue_key = "minio:upload:queue"
            transfer_id = str(uuid.uuid4())
            redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
            redis_client.lpush(queue_key, transfer_id)
            
            # Déclencher la tâche de traitement sur tous les workers pour maximiser les chances
            # qu'un worker libre prenne la tâche rapidement
            from app.tasks.storage.tasks import process_multipart_uploads
            
            # Liste des files d'attente de chaque worker
            worker_queues = ['storage_worker1', 'storage_worker2', 'storage_worker3', 'storage_worker4']
            
            # Déclencher une tâche sur chaque queue de worker avec un léger délai
            for i, queue in enumerate(worker_queues):
                # Petite latence entre chaque worker pour qu'ils ne se marchent pas dessus
                from datetime import timedelta
                from datetime import datetime
                eta = datetime.utcnow() + timedelta(seconds=i * 1)
                
                # Envoyer la tâche à ce worker spécifique
                process_multipart_uploads.apply_async(
                    eta=eta,
                    queue=queue
                )
                logging.info(f"Tâche de traitement envoyée au worker {i+1} (queue: {queue})")
            
            logging.info(f"Fichier {object_name} ajouté à la file d'attente ({transfer_id})")
            storage_operations.labels(operation='store', status='queued').inc()
            return True
            
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout à la file d'attente: {str(e)}")
            storage_operations.labels(operation='store', status='failed').inc()
            return False
    
    def process_multipart_upload(self, transfer_id: str) -> bool:
        """Traite un téléchargement multipart depuis la file d'attente
        
        Args:
            transfer_id: ID du transfert dans Redis
            
        Returns:
            True si le transfert a réussi, False sinon
        """
        import json
        import math
        import io
        import redis
        
        try:
            # Créer une connexion Redis synchrone
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_SESSION_DB
            )
            
            # Récupérer les informations de transfert
            transfer_info_json = redis_client.get(f"minio:transfer:{transfer_id}")
            if not transfer_info_json:
                logging.error(f"Aucune information de transfert trouvée pour {transfer_id}")
                return False
            
            transfer_info = json.loads(transfer_info_json.decode('utf-8'))
            file_path = transfer_info['file_path']
            object_name = transfer_info['object_name']
            file_size = transfer_info['file_size']
            part_size = transfer_info['part_size']
            uploaded_parts = transfer_info.get('uploaded_parts', [])
            
            # Vérifier que le fichier existe toujours
            if not os.path.exists(file_path):
                logging.error(f"Fichier source introuvable: {file_path}")
                redis_client.delete(f"minio:transfer:{transfer_id}")
                redis_client.lpush("minio:upload:failed", transfer_id)
                return False
            
            # Initialiser ou continuer le téléchargement multipart
            upload_id = transfer_info.get('upload_id')
            if not upload_id:
                try:
                    upload_id = self.client.create_multipart_upload(
                        self.fits_bucket, object_name, {'content-type': 'application/fits'})
                    transfer_info['upload_id'] = upload_id
                    redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                    logging.info(f"Téléchargement multipart initialisé: {upload_id} pour {object_name}")
                except Exception as e:
                    logging.error(f"Erreur lors de l'initialisation du téléchargement multipart: {str(e)}")
                    transfer_info['status'] = 'error'
                    transfer_info['last_error'] = str(e)
                    transfer_info['attempts'] = transfer_info.get('attempts', 0) + 1
                    redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                    redis_client.lpush("minio:upload:failed", transfer_id)
                    return False
            
            # Calculer les parties déjà téléchargées et celles restantes
            completed_part_numbers = [p['part_number'] for p in uploaded_parts]
            total_parts = math.ceil(file_size / part_size)
            
            logging.info(f"Téléchargement multipart: {len(completed_part_numbers)}/{total_parts} parties terminées pour {object_name}")
            
            # Télécharger les parties manquantes
            with open(file_path, 'rb') as f:
                for part_number in range(1, total_parts + 1):
                    if part_number in completed_part_numbers:
                        continue  # Partie déjà téléchargée
                    
                    # Positionner le curseur pour cette partie
                    f.seek((part_number - 1) * part_size)
                    
                    # Lire le contenu de la partie
                    part_data = f.read(part_size)
                    
                    if not part_data:
                        logging.warning(f"Partie {part_number} vide, fin du fichier atteinte")
                        break
                    
                    try:
                        # Télécharger la partie
                        etag = self.client.put_object_part(
                            self.fits_bucket, object_name, upload_id, part_number, 
                            io.BytesIO(part_data), len(part_data))
                        
                        # Enregistrer l'information de la partie
                        uploaded_parts.append({
                            'part_number': part_number,
                            'etag': etag,
                            'size': len(part_data)
                        })
                        
                        # Mettre à jour l'état dans Redis
                        transfer_info['uploaded_parts'] = uploaded_parts
                        redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                        
                        # Log de progression
                        progress = len(uploaded_parts) / total_parts * 100
                        logging.info(f"{object_name}: Partie {part_number}/{total_parts} téléchargée ({progress:.1f}%)")
                    except Exception as e:
                        logging.error(f"Erreur lors du téléchargement de la partie {part_number}: {str(e)}")
                        # Enregistrer l'erreur et arrêter
                        transfer_info['last_error'] = f"Partie {part_number}: {str(e)}"
                        transfer_info['status'] = 'error'
                        transfer_info['attempts'] = transfer_info.get('attempts', 0) + 1
                        redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                        redis_client.lpush("minio:upload:retry", transfer_id)
                        return False
            
            # Vérifier si toutes les parties ont été téléchargées
            if len(uploaded_parts) != total_parts:
                logging.warning(f"Téléchargement incomplet: {len(uploaded_parts)}/{total_parts} parties pour {object_name}")
                return False
            
            # Finaliser le téléchargement
            try:
                # Trier les parties par numéro
                parts = [{'PartNumber': p['part_number'], 'ETag': p['etag']} 
                        for p in sorted(uploaded_parts, key=lambda x: x['part_number'])]
                
                self.client.complete_multipart_upload(
                    self.fits_bucket, object_name, upload_id, parts)
                
                # Nettoyer Redis
                redis_client.delete(f"minio:transfer:{transfer_id}")
                
                logging.info(f"Téléchargement multipart terminé pour {object_name}")
                storage_operations.labels(operation='store_multipart', status='success').inc()
                return True
            except Exception as e:
                logging.error(f"Erreur lors de la finalisation du téléchargement multipart: {str(e)}")
                transfer_info['last_error'] = f"Finalisation: {str(e)}"
                transfer_info['status'] = 'error'
                transfer_info['attempts'] = transfer_info.get('attempts', 0) + 1
                redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                redis_client.lpush("minio:upload:retry", transfer_id)
                storage_operations.labels(operation='store_multipart', status='failed').inc()
                return False
                
        except Exception as e:
            # Gestion globale des erreurs
            try:
                logging.error(f"Erreur globale multipart pour {transfer_id}: {str(e)}")
                # Incrémenter le compteur de tentatives
                transfer_info = json.loads(redis_client.get(f"minio:transfer:{transfer_id}").decode('utf-8'))
                transfer_info['attempts'] = transfer_info.get('attempts', 0) + 1
                transfer_info['last_error'] = str(e)
                transfer_info['status'] = 'error'
                
                # Limiter les tentatives
                if transfer_info['attempts'] < 5:
                    redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                    # Remettre en file d'attente avec délai
                    redis_client.lpush("minio:upload:retry", transfer_id)
                else:
                    redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                    redis_client.lpush("minio:upload:failed", transfer_id)
            except Exception:
                logging.exception("Erreur catastrophique dans process_multipart_upload")
                
            storage_operations.labels(operation='store_multipart', status='failed').inc()
            return False

    def store_preview(self, data: bytes, object_name: str, content_type: str = "image/png") -> bool:
        """Stocke une preview dans MinIO"""
        with storage_operation_duration.labels(operation='store_preview').time():
            try:
                # Utilisation de put_object avec les données en mémoire
                from io import BytesIO
                data_stream = BytesIO(data)
                
                self.client.put_object(
                    self.preview_bucket,
                    object_name,
                    data_stream,
                    length=len(data),
                    content_type=content_type
                )
                
                logging.info(f"Successfully stored preview {object_name} in MinIO")
                storage_operations.labels(operation='store_preview', status='success').inc()
                return True

            except Exception as e:
                logging.error(f"Error storing preview {object_name}: {str(e)}")
                storage_operations.labels(operation='store_preview', status='failed').inc()
                return False

    def get_fits_file(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Récupère un fichier FITS depuis MinIO"""
        with storage_operation_duration.labels(operation='retrieve').time():
            try:
                stat = self.client.stat_object(self.fits_bucket, object_name)
                obj = self.client.get_object(self.fits_bucket, object_name)
                
                storage_operations.labels(operation='retrieve', status='success').inc()
                return {
                    "data": obj.read(),
                    "size": stat.size,
                    "content_type": stat.content_type
                }
            except Exception as e:
                logging.error(f"Error retrieving file {object_name}: {str(e)}")
                storage_operations.labels(operation='retrieve', status='failed').inc()
                return None
            
    def get_preview(self, object_name: str, bucket_name: str = "fits-files") -> Optional[Dict[str, Any]]:
        """Récupère une preview depuis MinIO"""
        with storage_operation_duration.labels(operation='retrieve_preview').time():
            try:
                # Utiliser le bucket spécifié explicitement
                stat = self.client.stat_object(bucket_name, object_name)
                obj = self.client.get_object(bucket_name, object_name)
                
                # Lecture des données
                preview_data = obj.read()
                
                # Génération de l'URL présignée avec gestion d'erreurs
                try:
                    presigned_url = self.client.presigned_get_object(
                        bucket_name,
                        object_name,
                        expires=timedelta(hours=1)
                    )
                except Exception as e:
                    logging.error(f"Error generating presigned URL for {object_name}: {str(e)}")
                    presigned_url = None
                
                storage_operations.labels(operation='retrieve_preview', status='success').inc()
                return {
                    "data": preview_data,
                    "size": stat.size,
                    "content_type": stat.content_type,
                    "url": presigned_url
                }
            except Exception as e:
                logging.error(f"Error retrieving preview {object_name} from {bucket_name}: {str(e)}")
                storage_operations.labels(operation='retrieve_preview', status='failed').inc()
            return None



    def delete_fits_file(self, object_name: str) -> bool:
        """Supprime un fichier FITS de MinIO"""
        with storage_operation_duration.labels(operation='delete').time():
            try:
                self.client.remove_object(self.fits_bucket, object_name)
                logging.info(f"Successfully deleted {object_name} from MinIO")
                storage_operations.labels(operation='delete', status='success').inc()
                return True
            except Exception as e:
                logging.error(f"Error deleting file {object_name}: {str(e)}")
                storage_operations.labels(operation='delete', status='failed').inc()
                return False

    async def check_files_exist(self, target_id: str, preset_id: str) -> dict:
        """
        Vérifie si les fichiers nécessaires pour une cible et un preset donnés existent déjà dans MinIO.
        
        Args:
            target_id: ID de la cible
            preset_id: ID du preset (non utilisé actuellement)
            
        Returns:
            Un dictionnaire contenant :
            - exists: True si des fichiers FITS existent, False sinon
            - fits_files: Liste des chemins des fichiers FITS trouvés 
            - jpg_files: Liste des chemins des fichiers JPG trouvés
        """
        logger = logging.getLogger("app.services.storage")
        logger.info(f"Vérification des fichiers existants pour target_id={target_id}, preset_id={preset_id}")
        
        # Initialiser le résultat
        result = {
            "exists": False,
            "fits_files": [],
            "jpg_files": []
        }
        
        try:
            # Vérifier si le bucket fits existe
            if not self.client.bucket_exists(self.fits_bucket):
                logger.warning(f"Le bucket {self.fits_bucket} n'existe pas")
                return result
                
            # Lister tous les objets dans le répertoire de la cible
            target_id_str = str(target_id)
            logger.info(f"Recherche de fichiers avec préfixe {target_id_str}/")
            
            try:
                objects = list(self.client.list_objects(
                    self.fits_bucket, 
                    prefix=f"{target_id_str}/",
                    recursive=True
                ))
                
                logger.info(f"Trouvé {len(objects)} objets pour la cible {target_id_str}")
                
                # Identifier les fichiers par extension
                for obj in objects:
                    object_name = obj.object_name
                    logger.info(f"Fichier trouvé: {object_name}")
                    if object_name.endswith(".fits") or object_name.endswith(".fit"):
                        result["fits_files"].append(object_name)
                    elif object_name.endswith(".jpg") or object_name.endswith(".jpeg"):
                        result["jpg_files"].append(object_name)
                
                # On considère que la cible existe si on a au moins un fichier FITS
                result["exists"] = len(result["fits_files"]) > 0
                
                logger.info(f"Résultat de la vérification: {result}")
                return result
                
            except Exception as e:
                logger.exception(f"Erreur lors de la liste des objets MinIO: {str(e)}")
                return result
            
        except Exception as e:
            logger.exception(f"Erreur lors de la vérification des fichiers: {str(e)}")
            return result
