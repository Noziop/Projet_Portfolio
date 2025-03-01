# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.monitoring import setup_monitoring
from app.services.storage.service import StorageService
from app.db.init_db import init_db

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour le développement, à restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring avant d'inclure les routes
instrumentator = setup_monitoring(app)

# Inclusion des routes API
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Stellar Studio API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    # Initialisation du cache Redis
    from app.core.cache import get_redis_client
    logger.info("Initialisation du cache Redis...")
    redis_client = get_redis_client()
    if redis_client:
        logger.info("Cache Redis initialisé avec succès !")
    else:
        logger.warning("Impossible d'initialiser le cache Redis, utilisation du fallback en mémoire")
    
    # Initialisation de la base de données
    logger.info("Initialisation de la base de données...")
    await init_db()
    logger.info("Base de données initialisée avec succès !")
    
    # Debug : afficher toutes les routes
    routes = [{"path": route.path, "name": route.name} for route in app.routes]
    logger.info(f"Routes disponibles: {routes}")

    # Test du StorageService
    logger.info("--- Début du test StorageService ---")
    storage_service = StorageService()

    test_file_path = "test_file.txt"
    test_object_name = "test-object.txt"

    # 1. Créer un fichier de test local
    try:
        with open(test_file_path, "w") as f:
            f.write("Ceci est un fichier de test pour MinIO.")
        logger.info(f"Fichier de test local '{test_file_path}' créé.")
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier de test local: {e}")
        return

    # 2. Stocker le fichier dans Minio
    try:
        if storage_service.store_fits_file(test_file_path, test_object_name):
            logger.info(f"Fichier '{test_file_path}' stocké avec succès dans MinIO sous le nom '{test_object_name}'.")
        else:
            logger.error(f"Échec du stockage du fichier '{test_file_path}' dans MinIO.")
    except Exception as e:
        logger.error(f"Erreur lors du stockage du fichier dans MinIO: {e}")

    # 3. Récupérer le fichier depuis Minio
    try:
        file_data = storage_service.get_fits_file(test_object_name)
        if file_data:
            retrieved_content = file_data["data"].decode('utf-8')
            logger.info(f"Fichier '{test_object_name}' récupéré depuis MinIO avec succès.")
            logger.info(f"Contenu récupéré: '{retrieved_content}'")
            assert retrieved_content == "Ceci est un fichier de test pour MinIO.", "Contenu du fichier récupéré incorrect !"
        else:
            logger.error(f"Échec de la récupération du fichier '{test_object_name}' depuis MinIO.")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du fichier depuis MinIO: {e}")

    # 4. Supprimer le fichier de Minio
    try:
        if storage_service.delete_fits_file(test_object_name):
            logger.info(f"Fichier '{test_object_name}' supprimé de MinIO avec succès.")
        else:
            logger.error(f"Échec de la suppression du fichier '{test_object_name}' de MinIO.")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du fichier de MinIO: {e}")

    # 5. Supprimer le fichier de test local
    try:
        os.remove(test_file_path)
        logger.info(f"Fichier de test local '{test_file_path}' supprimé.")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du fichier de test local: {e}")

    logger.info("--- Fin du test StorageService ---")

@app.on_event("shutdown")
async def shutdown_event():
    """Ferme les connexions à la base de données"""
    logger.info("Fermeture des connexions à la base de données...")
    from app.db.session import engine
    await engine.dispose()
    logger.info("Connexions fermées avec succès !")
