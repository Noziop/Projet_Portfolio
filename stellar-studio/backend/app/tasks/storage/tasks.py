# app/tasks/storage/tasks.py
import time
import json
import random
import logging
import redis
import uuid
import os
from celery import shared_task, current_task
from datetime import datetime, timedelta
import socket

from app.core.celery import celery_app
from app.core.config import settings
from app.services.storage.service import StorageService

# Client Redis synchrone pour les tâches Celery
_redis_client = None

def get_redis_client():
    """Récupère ou crée une connexion Redis synchrone"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_SESSION_DB
        )
    return _redis_client

# Identification du worker par son ID dans la queue
def get_worker_number():
    """
    Récupère le numéro d'identification du worker actuel.
    """
    # 1. Essayer d'abord de récupérer l'ID à partir de la variable d'environnement
    worker_id = os.environ.get("CELERY_WORKER_ID")
    
    if worker_id:
        return int(worker_id)
        
    # 2. Utiliser le hostname comme identifiant unique (format: celery-download-X)
    hostname = socket.gethostname()
    if '-' in hostname:
        try:
            # Extraire le numéro à partir du hostname (ex: celery-download-2 -> 2)
            parts = hostname.split('-')
            if len(parts) > 2:
                worker_id = int(parts[-1])
                return worker_id
        except (ValueError, IndexError):
            pass
    
    # 3. Fallback: Générer un ID basé sur le hash du hostname
    return (hash(hostname) % 4) + 1

@celery_app.task(name="app.tasks.storage.tasks.process_multipart_uploads", bind=True, acks_late=True)
def process_multipart_uploads(self):
    """
    Tâche périodique qui traite UN SEUL transfert multipart en attente.
    Chaque worker traitera un seul fichier, puis renverra une autre tâche pour traiter le suivant.
    """
    # Identifier ce worker
    worker_id = get_worker_number()
    worker_name = f"Worker-{worker_id}"
    worker_uuid = str(uuid.uuid4())[:8]

    logger = logging.getLogger("app.tasks.storage")
    logger.info(f"[{worker_name} {worker_uuid}] Recherche d'un transfert à traiter...")
    
    # Obtenir les transferts en attente
    redis_client = get_redis_client()
    
    # Stocker le worker actif dans Redis pour le monitoring
    redis_client.hset("minio:active_workers", worker_uuid, f"{worker_name}:{datetime.now().isoformat()}")
    redis_client.expire("minio:active_workers", 300)  # Expire après 5 minutes d'inactivité
    
    # Récupérer les clés des transferts en attente
    transfer_keys = redis_client.keys("minio:transfer:*:info")
    if not transfer_keys:
        logger.info(f"[{worker_name} {worker_uuid}] Aucun transfert en attente.")
        return True
    
    # Ajouter un peu d'aléatoire pour éviter que tous les workers traitent les fichiers dans le même ordre
    random.shuffle(transfer_keys)
    
    # Traiter UN SEUL transfert
    for key in transfer_keys:
        transfer_id = key.decode().split(":")[2]
        
        # Vérifier si ce transfert est déjà en cours de traitement par un autre worker
        lock_key = f"minio:lock:{transfer_id}"
        if redis_client.exists(lock_key):
            continue
            
        # Essayer d'acquérir le verrou
        lock_acquired = redis_client.set(lock_key, worker_uuid, ex=3600, nx=True)
        if not lock_acquired:
            continue
        
        try:
            # Log le début du traitement
            logger.info(f"[{worker_name} {worker_uuid}] Traitement du transfert {transfer_id}...")
            
            # Traiter le transfert
            storage_service = StorageService()
            success = storage_service.process_multipart_upload(transfer_id)
            
            if success:
                logger.info(f"[{worker_name} {worker_uuid}] Transfert {transfer_id} complété avec succès.")
            else:
                logger.error(f"[{worker_name} {worker_uuid}] Échec du transfert {transfer_id}.")
                
            # Vérifier s'il reste d'autres transferts
            remaining = len(redis_client.keys("minio:transfer:*:info"))
            if remaining > 0:
                logger.info(f"[{worker_name} {worker_uuid}] {remaining} transferts restants, planification d'une nouvelle tâche.")
                # Déclencher une nouvelle tâche immédiatement pour traiter le reste
                process_multipart_uploads.apply_async(countdown=1)
                
            return True
            
        except Exception as e:
            logger.exception(f"[{worker_name} {worker_uuid}] Erreur pendant le traitement du transfert {transfer_id}: {str(e)}")
        finally:
            # Supprimer le verrou quoi qu'il arrive
            redis_client.delete(lock_key)
    
    # Si on arrive ici, c'est que tous les transferts étaient déjà verrouillés
    logger.info(f"[{worker_name} {worker_uuid}] Tous les transferts sont déjà en cours de traitement.")
    return True

@celery_app.task(name="app.tasks.storage.tasks.check_failed_transfers", bind=True)
def check_failed_transfers(self):
    """Tâche périodique qui vérifie et retente les transferts échoués"""
    logger = logging.getLogger("app.tasks.storage")
    redis_client = get_redis_client()
    
    # Récupérer la liste des transferts échoués
    failed_key = "minio:upload:failed"
    failed_count = redis_client.llen(failed_key)
    
    if failed_count > 0:
        logger.info(f"{failed_count} transferts échoués en attente de reprise")
        
        # Déplacer jusqu'à 5 transferts échoués vers la file de reprise
        for _ in range(min(5, failed_count)):
            transfer_id = redis_client.rpop(failed_key)
            if transfer_id:
                transfer_id = transfer_id.decode('utf-8')
                # Récupérer les infos du transfert
                transfer_info_json = redis_client.get(f"minio:transfer:{transfer_id}")
                if transfer_info_json:
                    # Marquer comme nouvelle tentative
                    transfer_info = json.loads(transfer_info_json.decode('utf-8'))
                    transfer_info['status'] = 'retry'
                    transfer_info['last_retry'] = time.time()
                    redis_client.set(f"minio:transfer:{transfer_id}", json.dumps(transfer_info))
                    # Ajouter à la file d'attente de reprise
                    redis_client.lpush("minio:upload:retry", transfer_id)
                    logger.info(f"Transfert {transfer_id} remis en file d'attente pour nouvelle tentative")
    else:
        logger.info("Aucun transfert échoué en attente") 