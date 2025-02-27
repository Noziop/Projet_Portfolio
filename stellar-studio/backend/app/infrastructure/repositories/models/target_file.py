from sqlalchemy import Column, String, BigInteger, Boolean, JSON, ForeignKey, CheckConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.mysql import CHAR
from app.db.base_class import Base
import json
import os

class TargetFile(Base):
    """Modèle SQLAlchemy pour les fichiers FITS associés aux cibles.
    
    Ce modèle gère les métadonnées et les références aux fichiers FITS
    stockés dans le système, incluant leur statut de téléchargement et
    leur stockage dans MinIO.
    """

    __tablename__ = "target_files"

    __table_args__ = (
        CheckConstraint('file_size >= 0', name='check_positive_size'),
        CheckConstraint(
            "JSON_VALID(fits_metadata)", 
            name='check_valid_metadata_json'
        ),
        CheckConstraint(
            "file_path REGEXP '^[a-zA-Z0-9/_.-]+$'",
            name='check_valid_file_path'
        ),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    # Colonnes - Relations principales
    target_id = Column(
        CHAR(36), 
        ForeignKey("targets.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID de la cible associée"
    )
    
    filter_id = Column(
        CHAR(36), 
        ForeignKey("filters.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="ID du filtre utilisé"
    )

    # Colonnes - Informations fichier
    file_path = Column(
        String(255), 
        nullable=False, 
        index=True, 
        unique=True,
        comment="Chemin relatif du fichier dans le stockage"
    )
    
    file_size = Column(
        BigInteger, 
        nullable=False, 
        default=0,
        comment="Taille du fichier en octets"
    )
    
    mast_id = Column(
        String(255), 
        index=True,
        comment="Identifiant MAST du fichier"
    )

    # Colonnes - États
    is_downloaded = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        index=True,
        comment="Indique si le fichier a été téléchargé"
    )
    
    in_minio = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        index=True,
        comment="Indique si le fichier est stocké dans MinIO"
    )
    
    # Colonnes - Métadonnées
    fits_metadata = Column(
        JSON, 
        nullable=False, 
        default={},
        comment="Métadonnées FITS au format JSON"
    )

    # Relations
    target = relationship(
        "Target", 
        back_populates="files",
        lazy="joined"
    )
    
    filter = relationship(
        "Filter", 
        back_populates="target_files",
        lazy="joined"
    )
    
    preset_files = relationship(
        "PresetTargetFile", 
        back_populates="target_file",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Validateurs
    @validates('file_path')
    def validate_file_path(self, key, path):
        """Valide le format du chemin de fichier."""
        if not path:
            raise ValueError("Le chemin de fichier ne peut pas être vide")
        
        # Vérification des caractères autorisés
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/._-")
        if not all(c in allowed_chars for c in path):
            raise ValueError("Le chemin contient des caractères non autorisés")
        
        # Normalisation du chemin
        path = os.path.normpath(path)
        
        # Vérification de la longueur
        if len(path) > 255:
            raise ValueError("Le chemin est trop long (max 255 caractères)")
            
        return path

    @validates('file_size')
    def validate_file_size(self, key, size):
        """Valide la taille du fichier."""
        if not isinstance(size, (int, float)) or size < 0:
            raise ValueError("La taille du fichier doit être un nombre positif")
        return int(size)

    @validates('fits_metadata')
    def validate_fits_metadata(self, key, metadata):
        """Valide les métadonnées FITS."""
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise ValueError("Les métadonnées doivent être un JSON valide")
        
        if not isinstance(metadata, dict):
            raise ValueError("Les métadonnées doivent être un dictionnaire")
        
        # Validation des champs requis
        required_fields = {'SIMPLE', 'BITPIX', 'NAXIS'}
        if not all(field in metadata for field in required_fields):
            raise ValueError(f"Métadonnées FITS incomplètes. Champs requis: {required_fields}")
            
        return metadata

    @validates('mast_id')
    def validate_mast_id(self, key, mast_id):
        """Valide l'identifiant MAST."""
        if mast_id and len(mast_id) > 255:
            raise ValueError("L'identifiant MAST est trop long")
        return mast_id

    def __repr__(self):
        return (
            f"<TargetFile("
            f"target_id='{self.target_id}', "
            f"filter_id='{self.filter_id}', "
            f"downloaded={self.is_downloaded}, "
            f"in_minio={self.in_minio})>"
        )

    # Méthodes utilitaires
    @property
    def full_path(self):
        """Retourne le chemin complet du fichier."""
        return os.path.join("/data/fits", self.file_path)

    @property
    def minio_path(self):
        """Retourne le chemin dans MinIO."""
        return f"fits/{self.target_id}/{os.path.basename(self.file_path)}"

    def update_download_status(self, is_downloaded: bool, file_size: int = None):
        """Met à jour le statut de téléchargement et la taille."""
        self.is_downloaded = is_downloaded
        if file_size is not None:
            self.file_size = file_size

    def update_minio_status(self, in_minio: bool):
        """Met à jour le statut de stockage MinIO."""
        self.in_minio = in_minio

# Event Listeners
@event.listens_for(TargetFile, 'before_insert')
def validate_file_status(mapper, connection, target):
    """Vérifie la cohérence des statuts avant insertion."""
    if target.in_minio and not target.is_downloaded:
        raise ValueError("Un fichier ne peut pas être dans MinIO sans être téléchargé")

@event.listens_for(TargetFile, 'before_update')
def check_status_transition(mapper, connection, target):
    """Vérifie les transitions de statut valides."""
    if hasattr(target, '_sa_instance_state'):
        if 'in_minio' in target._sa_instance_state.committed_state:
            old_minio = target._sa_instance_state.committed_state['in_minio']
            if old_minio and not target.in_minio:
                raise ValueError("Impossible de supprimer un fichier de MinIO via ce modèle")

class TargetFileError(Exception):
    """Exception personnalisée pour les erreurs liées aux fichiers cibles."""
    pass
