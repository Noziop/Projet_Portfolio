# app/services/storage/service.py
import os
from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_URL.replace('http://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        # Utiliser la variable d'environnement pour le nom du bucket
        self.fits_bucket = os.getenv('MINIO_BUCKET_NAME', 'fits-files')
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
            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}")
                return False

            self.client.fput_object(
                self.fits_bucket,
                object_name,
                file_path,
                content_type="application/fits"
            )
            logging.info(f"Successfully stored {object_name} in MinIO")
            return True
        except S3Error as e:
            logging.error(f"Error storing FITS file {object_name}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error storing file {object_name}: {str(e)}")
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
            logging.error(f"Error retrieving FITS file {object_name}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error retrieving file {object_name}: {str(e)}")
            return None

    def delete_fits_file(self, object_name: str) -> bool:
        """Supprime un fichier FITS de MinIO"""
        try:
            self.client.remove_object(self.fits_bucket, object_name)
            logging.info(f"Successfully deleted {object_name} from MinIO")
            return True
        except S3Error as e:
            logging.error(f"Error deleting FITS file {object_name}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error deleting file {object_name}: {str(e)}")
            return False

