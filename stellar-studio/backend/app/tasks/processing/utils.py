# app/tasks/processing/utils.py
import numpy as np
from PIL import Image
import io
import logging
from typing import Dict, Any

from app.services.storage.service import StorageService

# Configuration du logging
utils_logger = logging.getLogger('app.task.processing.utils')

def auto_stf(data: np.ndarray, target_background: float = 0.25, shadow_protection: float = 0.0, tolerance: float = 0.0015) -> np.ndarray:
    """
    Implémente une version de l'AutoSTF inspirée de PixInsight.
    
    Args:
        data: L'image d'entrée en numpy array
        target_background: Niveau cible pour le fond de ciel (0.25 = 25%)
        shadow_protection: Protection des ombres (0-1)
        tolerance: Tolérance pour la convergence
        
    Returns:
        Image étirée
    """
    # 1. Calcul des statistiques robustes
    median = np.median(data)
    mad = np.median(np.abs(data - median))
    
    # 2. Estimation du bruit
    noise = 1.4826 * mad  # Estimation robuste de l'écart-type
    
    # 3. Détection du fond de ciel (background)
    # Utilise une approche itérative pour trouver le mode
    hist, bins = np.histogram(data, bins=1000)
    peak_idx = np.argmax(hist)
    background = (bins[peak_idx] + bins[peak_idx + 1]) / 2
    
    # 4. Détection des pixels significatifs
    # Pixels au-dessus du niveau de bruit
    significant_pixels = data[data > (background + 3 * noise)]
    
    if len(significant_pixels) > 0:
        # 5. Calcul du point de référence pour les hautes lumières
        # Utilise le 99.5 percentile des pixels significatifs
        highlights = np.percentile(significant_pixels, 99.5)
    else:
        highlights = background + 3 * noise
    
    # 6. Protection des ombres
    shadows = background + shadow_protection * (highlights - background)
    
    # 7. Application de la transformation
    # Ajuste le background au niveau cible
    m = target_background / (background - shadows)
    b = -m * shadows
    
    # Application de la transformation
    stretched = m * data + b
    
    return np.clip(stretched, 0, 1)

# Alias pour la compatibilité avec le code existant
apply_stf = auto_stf

def save_preview(rgb_data: np.ndarray, storage_service: StorageService, job_id: str) -> str:
    """Sauvegarde une preview dans MinIO"""
    # Conversion en PNG en mémoire
    preview_data = (rgb_data * 255).astype(np.uint8)
    image = Image.fromarray(preview_data)
    
    # Sauvegarde temporaire en mémoire
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Chemin dans MinIO
    preview_path = f"previews/{job_id}_hoo_preview.png"
    
    # Stockage dans MinIO
    storage_service.store_preview(
        img_byte_arr.getvalue(),
        preview_path,
        content_type="image/png"
    )
    
    utils_logger.info(f"Aperçu sauvegardé: {preview_path}")
    return preview_path

def get_services_sync():
    """Version synchrone pour obtenir les services nécessaires"""
    from app.db.session import SyncSessionLocal
    from app.services.storage.service import StorageService
    from app.core.ws.manager import ConnectionManager
    
    session = SyncSessionLocal()
    storage_service = StorageService()
    ws_manager = ConnectionManager()
    
    utils_logger.info("Services synchrones initialisés pour le traitement")
    return session, storage_service, ws_manager
