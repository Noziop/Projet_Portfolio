# app/infrastructure/repositories/models/__init__.py
from app.infrastructure.repositories.models.base import *

# Import de tous les modèles
from app.infrastructure.repositories.models.user import User
from app.infrastructure.repositories.models.filter import Filter
from app.infrastructure.repositories.models.preset import Preset
from app.infrastructure.repositories.models.preset_target_file import PresetTargetFile
from app.infrastructure.repositories.models.target import Target
from app.infrastructure.repositories.models.target_file import TargetFile
from app.infrastructure.repositories.models.telescope import SpaceTelescope
from app.infrastructure.repositories.models.workflow import Workflow
from app.infrastructure.repositories.models.processing import ProcessingJob
from app.infrastructure.repositories.models.task import Task

# Configuration des mappers pour résoudre les dépendances circulaires
from sqlalchemy.orm import configure_mappers
configure_mappers()

# Export pour faciliter l'import dans d'autres modules
__all__ = [
    'User',
    'Filter',
    'Preset',
    'PresetTargetFile',
    'Target',
    'TargetFile',
    'SpaceTelescope',
    'Workflow',
    'ProcessingJob',
    'Task'
]