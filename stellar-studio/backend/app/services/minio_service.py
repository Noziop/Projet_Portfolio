# app/services/minio_service.py
from minio import Minio
from app.core.config import settings

def get_minio_client():
    return Minio(
        "minio:9000",  # Utiliser le nom du service dans docker-compose
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

def init_minio():
    client = get_minio_client()
    try:
        # Créer le bucket s'il n'existe pas
        if not client.bucket_exists("fits-files"):
            client.make_bucket("fits-files")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de MinIO : {e}")
