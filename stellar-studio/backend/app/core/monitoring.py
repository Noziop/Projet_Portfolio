# app/core/monitoring.py
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, REGISTRY

logger = logging.getLogger(__name__)
# Configurer le niveau de log
logging.basicConfig(level=logging.DEBUG)

def setup_monitoring(app):
    logger.debug("Démarrage de la configuration du monitoring...")
    
    instrumentator = Instrumentator()
    
    logger.debug("Instrumentation de l'application...")
    instrumentator.instrument(app)
    
    logger.debug("Exposition des métriques...")
    instrumentator.expose(app)
    
    logger.debug("Configuration du monitoring terminée")
    
    return instrumentator
