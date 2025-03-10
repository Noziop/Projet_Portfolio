# app/tasks/processing/__init__.py

# Exportation des fonctions utilitaires
from .utils import auto_stf, apply_stf, save_preview, get_services_sync

# Les tâches que nous allons implémenter dans les modules suivants
from .presets import process_hoo_preset, process_rgb_preset
from .previews import generate_channel_previews
from .validation import wait_user_validation

# Pour la compatibilité avec l'existant
# Ces imports permettent d'utiliser directement app.tasks.processing.process_hoo_preset
__all__ = [
    'auto_stf',
    'apply_stf',
    'save_preview',
    'get_services_sync',
    'process_hoo_preset',
    'process_rgb_preset',
    'generate_channel_previews',
    'wait_user_validation'
]
