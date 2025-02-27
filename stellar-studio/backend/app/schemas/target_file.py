# app/schemas/target_file.py
from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field, validator
from .filter import FilterResponse

class TargetFileBase(BaseModel):
    """Attributs communs pour tous les schemas TargetFile"""
    file_path: str = Field(..., description="Chemin du fichier dans MinIO")
    mast_id: str = Field(..., description="Identifiant MAST du fichier")
    file_size: Optional[int] = Field(None, description="Taille du fichier en bytes")
    is_downloaded: bool = Field(
        default=False,
        description="Indique si le fichier a été téléchargé depuis MAST"
    )
    in_minio: bool = Field(
        default=False,
        description="Indique si le fichier est stocké dans MinIO"
    )
    fits_metadata: Optional[Dict] = Field(
        None,
        description="Métadonnées FITS du fichier"
    )

class TargetFileCreate(TargetFileBase):
    """Schema pour la création d'un fichier cible"""
    target_id: UUID = Field(..., description="ID de la cible associée")
    filter_id: UUID = Field(..., description="ID du filtre utilisé")

    @validator('file_path')
    def validate_file_path(cls, v):
        if not v.endswith('.fits'):
            raise ValueError("Le chemin doit pointer vers un fichier FITS")
        return v

class TargetFileUpdate(BaseModel):
    """Schema pour la mise à jour d'un fichier cible"""
    file_size: Optional[int] = None
    is_downloaded: Optional[bool] = None
    in_minio: Optional[bool] = None
    fits_metadata: Optional[Dict] = None

class TargetFileInDB(TargetFileBase):
    """Schema pour un fichier cible en DB"""
    id: UUID
    target_id: UUID
    filter_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TargetFileResponse(TargetFileInDB):
    """Schema pour la réponse API"""
    target_name: Optional[str] = Field(None, description="Nom de la cible")
    filter: Optional[FilterResponse] = Field(None, description="Détails du filtre")
    download_url: Optional[str] = Field(
        None,
        description="URL présignée pour le téléchargement"
    )
    preview_url: Optional[str] = Field(
        None,
        description="URL de la preview si disponible"
    )

    class Config:
        from_attributes = True

class TargetFileStats(BaseModel):
    """Statistiques sur les fichiers d'une cible"""
    total_files: int = Field(..., description="Nombre total de fichiers")
    downloaded_files: int = Field(..., description="Nombre de fichiers téléchargés")
    total_size: int = Field(..., description="Taille totale en bytes")
    filters_count: Dict[str, int] = Field(
        ..., 
        description="Nombre de fichiers par filtre"
    )
