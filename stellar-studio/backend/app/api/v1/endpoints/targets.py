# app/api/v1/endpoints/targets.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response, BackgroundTasks, Header
from typing import List, Optional, Dict, Any
import time
import logging
import hashlib
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.target.service import TargetService
from app.services.storage.service import StorageService
from app.core.ws.manager import ConnectionManager
from app.schemas.target import TargetResponse, TargetListResponse, TargetCreate, TargetStatus
from app.domain.value_objects.target_types import ObjectType
from starlette.status import HTTP_304_NOT_MODIFIED, HTTP_200_OK
from app.core.cache import RedisCache
import json
from hashlib import md5

# Logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Durée de validité du cache en secondes
CACHE_TTL_SHORT = 60     # 1 minute pour les requêtes fréquentes
CACHE_TTL_MEDIUM = 300   # 5 minutes pour la plupart des requêtes
CACHE_TTL_LONG = 3600    # 1 heure pour les données rarement modifiées

def generate_cache_key(telescope_id: Optional[UUID] = None, object_type: Optional[ObjectType] = None) -> str:
    """Génère une clé de cache unique basée sur les paramètres de la requête"""
    params = f"telescope_id={telescope_id or 'all'}_object_type={object_type.value if object_type else 'all'}"
    return hashlib.md5(params.encode()).hexdigest()

@router.get("/", response_model=List[TargetResponse])
async def list_targets(
    response: Response,
    background_tasks: BackgroundTasks,
    telescope_id: Optional[UUID] = Query(None, description="Filtrer par télescope"),
    object_type: Optional[ObjectType] = Query(None, description="Filtrer par type d'objet"),
    status: Optional[TargetStatus] = None,
    if_none_match: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Liste les cibles disponibles, filtrable par télescope, type d'objet et statut avec support de cache Redis"""
    start_time = time.time()
    logger.info(f"Endpoint: GET /targets/ called with telescope_id={telescope_id}, object_type={object_type}")
    
    try:
        # Génération de la clé de cache basée sur les paramètres
        cache_params = {
            "telescope_id": str(telescope_id) if telescope_id else None,
            "object_type": object_type.value if object_type else None,
            "status": status.value if status else None
        }
        cache_key = md5(json.dumps(cache_params, sort_keys=True).encode()).hexdigest()
        
        # Vérifier le cache Redis
        cache_entry = RedisCache.get("targets", cache_key)
        
        # Si ETag fourni et correspond au cache, renvoyer 304 Not Modified
        if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
            logger.info(f"Redis cache hit with ETag - returning 304 (time: {time.time() - start_time:.3f}s)")
            return Response(status_code=HTTP_304_NOT_MODIFIED)
        
        # Si en cache, utiliser les données en cache
        if cache_entry:
            logger.info(f"Redis cache hit - returning cached data (time: {time.time() - start_time:.3f}s)")
            response.headers["ETag"] = cache_entry.get("etag")
            return cache_entry.get("data")
        
        # Sinon, exécuter la requête
        target_service = TargetService(
            session=db,
            storage_service=StorageService(),
            ws_manager=ConnectionManager()
        )
        
        if telescope_id:
            targets = await target_service.target_repository.get_by_telescope(telescope_id)
        elif object_type:
            targets = await target_service.target_repository.get_by_type(object_type)
        else:
            targets = await target_service.target_repository.get_all()
        
        # Convertir les objets Target en dictionnaires pour la réponse
        response_targets = []
        for target in targets:
            # Extraire les données de base de la cible
            target_dict = {
                "id": target.id,
                "name": target.name,
                "description": target.description,
                "catalog_name": target.catalog_name,
                "common_name": target.common_name,
                "coordinates_ra": target.coordinates_ra,
                "coordinates_dec": target.coordinates_dec,
                "object_type": target.object_type,
                "telescope_id": target.telescope_id,
                "status": target.status,
                "created_at": target.created_at,
                "updated_at": target.updated_at,
                "telescope_name": target.telescope.name if target.telescope else None,
                "coordinates": target.coordinates,
                "available_presets": []
            }
            
            # Récupérer les présets disponibles dans le format correct
            presets_data = await target_service.get_available_presets(target.id)
            for preset_data in presets_data:
                target_dict["available_presets"].append({
                    "target_id": preset_data["target_id"],
                    "preset_id": preset_data["preset_id"],
                    "is_available": preset_data["is_available"],
                    "preset": preset_data["preset"],
                    "required_filters": preset_data["required_filters"],
                    "missing_filters": []
                })
            
            response_targets.append(target_dict)
        
        # Mise à jour du cache Redis
        RedisCache.set("targets", cache_key, response_targets, ttl=CACHE_TTL_MEDIUM)
        
        # Récupérer l'ETag du cache
        updated_cache = RedisCache.get("targets", cache_key)
        if updated_cache and updated_cache.get("etag"):
            response.headers["ETag"] = updated_cache.get("etag")
            
        logger.info(f"Request completed in {time.time() - start_time:.3f}s")
        
        return response_targets
        
    except Exception as e:
        logger.error(f"Error in list_targets: {str(e)}")
        raise

@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: UUID,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'une cible par son ID avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour cette cible
    cache_key = f"target_{target_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("target", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for target {target_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for target {target_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    target = await target_service.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    # Extraire les données de base de la cible
    target_dict = {
        "id": target.id,
        "name": target.name,
        "description": target.description,
        "catalog_name": target.catalog_name,
        "common_name": target.common_name,
        "coordinates_ra": target.coordinates_ra,
        "coordinates_dec": target.coordinates_dec,
        "object_type": target.object_type,
        "telescope_id": target.telescope_id,
        "status": target.status,
        "created_at": target.created_at,
        "updated_at": target.updated_at,
        "telescope_name": target.telescope.name if target.telescope else None,
        "coordinates": target.coordinates,
        "available_presets": []
    }
    
    # Récupérer les présets disponibles dans le format correct
    presets_data = await target_service.get_available_presets(target.id)
    for preset_data in presets_data:
        target_dict["available_presets"].append({
            "target_id": preset_data["target_id"],
            "preset_id": preset_data["preset_id"],
            "is_available": preset_data["is_available"],
            "preset": preset_data["preset"],
            "required_filters": preset_data["required_filters"],
            "missing_filters": []
        })
    
    # Mise en cache Redis
    RedisCache.set("target", cache_key, target_dict, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("target", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Target {target_id} fetched in {time.time() - start_time:.3f}s")
    return target_dict

@router.get("/{target_id}/files")
async def get_target_files(
    target_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les fichiers associés à une cible avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour les fichiers de cette cible
    cache_key = f"target_files_{target_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("target_files", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for files of target {target_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for files of target {target_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    target_with_files = await target_service.get_target_with_files(target_id)
    if not target_with_files:
        raise HTTPException(status_code=404, detail="Cible non trouvée")
    
    # Convertir les objets SQLAlchemy en dictionnaires
    files_dict = []
    for file in target_with_files["files"]:
        file_dict = {
            "id": file.id,
            "target_id": file.target_id,
            "filter_id": file.filter_id,
            "file_path": file.file_path,
            "file_size": file.file_size,
            "mast_id": file.mast_id,
            "is_downloaded": file.is_downloaded,
            "in_minio": file.in_minio,
            "fits_metadata": file.fits_metadata,
            "created_at": file.created_at,
            "updated_at": file.updated_at,
            "filter_name": file.filter.name if file.filter else None,
            "filter_code": file.filter.code if file.filter else None,
            "filter_wavelength": file.filter.wavelength if file.filter else None,
            "filter_type": file.filter.filter_type if file.filter else None
        }
        files_dict.append(file_dict)
    
    # Mise en cache Redis
    RedisCache.set("target_files", cache_key, files_dict, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("target_files", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Files for target {target_id} fetched in {time.time() - start_time:.3f}s")
    return files_dict

@router.get("/{target_id}/presets")
async def get_target_presets(
    target_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les presets disponibles pour une cible avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour les presets de cette cible
    cache_key = f"target_presets_{target_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("target_presets", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for presets of target {target_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for presets of target {target_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    presets = await target_service.get_available_presets(target_id)
    if not presets:
        raise HTTPException(status_code=404, detail="Aucun preset disponible pour cette cible")
    
    # Mise en cache Redis
    RedisCache.set("target_presets", cache_key, presets, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("target_presets", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Presets for target {target_id} fetched in {time.time() - start_time:.3f}s")
    return presets

@router.get("/{target_id}/preview")
async def get_target_preview(
    target_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'URL de preview pour une cible avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour la preview de cette cible
    cache_key = f"target_preview_{target_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("target_preview", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for preview of target {target_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for preview of target {target_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    target_service = TargetService(
        session=db,
        storage_service=StorageService(),
        ws_manager=ConnectionManager()
    )
    
    preview_path = await target_service.generate_target_preview(target_id)
    if not preview_path:
        raise HTTPException(status_code=404, detail="Pas de preview disponible pour cette cible")
    
    result = {"preview_url": preview_path}
    
    # Mise en cache Redis - plus long car les previews changent rarement
    RedisCache.set("target_preview", cache_key, result, ttl=CACHE_TTL_LONG)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("target_preview", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Preview for target {target_id} fetched in {time.time() - start_time:.3f}s")
    return result
