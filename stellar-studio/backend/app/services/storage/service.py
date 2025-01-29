# app/services/storage/service.py
import os
from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional, Dict, Any

class StorageService:
    def __init__(self):
        self.client = Minio(
            # Utiliser uniquement le hostname:port sans chemin
            os.getenv('MINIO_URL', 'minio:9000').replace('http://', ''),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=False  # False car nous n'utilisons pas HTTPS en local
        )
        self.fits_bucket = "fits-files"
        self._ensure_bucket_exists(self.fits_bucket)

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """S'assure que le bucket existe, le crée si nécessaire"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logging.info(f"Bucket '{bucket_name}' created")
        except S3Error as e:
            logging.error(f"Error ensuring bucket exists: {str(e)}")
            raise

    def store_fits_file(self, file_path: str, object_name: str) -> bool:
        """Stocke un fichier FITS dans MinIO"""
        try:
            self.client.fput_object(
                self.fits_bucket,
                object_name,
                file_path
            )
            return True
        except S3Error as e:
            logging.error(f"Error storing FITS file: {str(e)}")
            return False

    def get_fits_file(self, object_name: str) -> Optional[Dict[str, Any]]:
        """Récupère un fichier FITS depuis MinIO"""
        try:
            obj = self.client.get_object(self.fits_bucket, object_name)
            return {
                "data": obj.read(),
                "size": obj.size,
                "content_type": obj.content_type
            }
        except S3Error as e:
            logging.error(f"Error retrieving FITS file: {str(e)}")
            return None

    def delete_fits_file(self, object_name: str) -> bool:
        """Supprime un fichier FITS de MinIO"""
        try:
            self.client.remove_object(self.fits_bucket, object_name)
            return True
        except S3Error as e:
            logging.error(f"Error deleting FITS file: {str(e)}")
            return False
