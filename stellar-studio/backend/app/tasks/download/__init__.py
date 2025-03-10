"""
Tâches Celery pour le téléchargement d'images MAST.
Ces tâches gèrent la recherche, la sélection et le téléchargement de fichiers depuis MAST.
"""

# Tâches individuelles
from .search import search_observations
from .select import select_files
from .download import download_chunk
from .finalize import finalize_download

# Orchestration du workflow
from .workflow import start_mast_download, create_download_tasks

# Compatibilité avec l'existant
from .workflow import start_mast_download as download_mast_files

__all__ = [
    'search_observations',
    'select_files',
    'download_chunk',
    'finalize_download',
    'start_mast_download',
    'create_download_tasks',
    'download_mast_files'  # Alias pour compatibilité
]
