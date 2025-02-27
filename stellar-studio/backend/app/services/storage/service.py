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

    def store_fits_file(self, file_path: str, object_name: str) -> bool:
        """Stocke un fichier FITS dans MinIO"""
        with storage_operation_duration.labels(operation='store').time():
            try:
                if not os.path.exists(file_path):
                    logging.error(f"File not found: {file_path}")
                    storage_operations.labels(operation='store', status='failed').inc()
                    return False

                # Mesure de la taille du fichier
                file_size = os.path.getsize(file_path)
                storage_file_size.observe(file_size)

                self.client.fput_object(
                    self.fits_bucket,
                    object_name,
                    file_path,
                    content_type="application/fits"
                )
                
                logging.info(f"Successfully stored {object_name} in MinIO")
                storage_operations.labels(operation='store', status='success').inc()
                return True

            except Exception as e:
                logging.error(f"Error storing file {object_name}: {str(e)}")
                storage_operations.labels(operation='store', status='failed').inc()
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
            
    def get_preview(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Récupère une preview depuis MinIO"""
        with storage_operation_duration.labels(operation='retrieve_preview').time():
            try:
                stat = self.client.stat_object(self.preview_bucket, object_name)
                obj = self.client.get_object(self.preview_bucket, object_name)
                
                # Lecture des données
                preview_data = obj.read()
                
                storage_operations.labels(operation='retrieve_preview', status='success').inc()
                return {
                    "data": preview_data,
                    "size": stat.size,
                    "content_type": stat.content_type,
                    # On peut ajouter une URL présignée pour le frontend
                    "url": self.client.presigned_get_object(
                        self.preview_bucket,
                        object_name,
                        expires=timedelta(hours=1)
                    )
                }
            except Exception as e:
                logging.error(f"Error retrieving preview {object_name}: {str(e)}")
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
