# app/api/v1/endpoints/telescopes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response, BackgroundTasks
from typing import List, Optional, Dict, Any
import time
import logging
import hashlib
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.telescope.service import TelescopeService
from app.schemas.telescope import TelescopeResponse, TelescopeListResponse
from starlette.status import HTTP_304_NOT_MODIFIED, HTTP_200_OK
from app.schemas.filter import FilterResponse
from app.schemas.preset import PresetResponse
from app.core.cache import RedisCache

# Logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Durée de validité du cache en secondes
CACHE_TTL_SHORT = 60     # 1 minute pour les requêtes fréquentes
CACHE_TTL_MEDIUM = 300   # 5 minutes pour la plupart des requêtes
CACHE_TTL_LONG = 3600    # 1 heure pour les données rarement modifiées

def generate_cache_key(status: Optional[str] = None, skip: int = 0, limit: int = 100) -> str:
    """Génère une clé de cache unique basée sur les paramètres de la requête"""
    params = f"status={status or 'all'}_skip={skip}_limit={limit}"
    return hashlib.md5(params.encode()).hexdigest()

async def refresh_cache_in_background(db: AsyncSession, status: Optional[str] = None):
    """Rafraîchit le cache en arrière-plan pour éviter les temps d'attente"""
    try:
        telescope_service = TelescopeService(db)
        if status:
            from app.domain.value_objects.telescope_types import TelescopeStatus
            status_enum = TelescopeStatus[status.upper()]
            telescopes = await telescope_service.get_by_status(status_enum)
        else:
            telescopes = await telescope_service.get_active_telescopes()
            
        # Mettre à jour le cache Redis
        current_time = time.time()
        
        # Mettre en cache la liste entière
        all_key = generate_cache_key(status=status)
        RedisCache.set("telescopes", all_key, telescopes, ttl=CACHE_TTL_MEDIUM)
        
        # Pré-calculer les résultats paginés courants (les 5 premières pages)
        for i in range(5):
            skip = i * 20
            key = generate_cache_key(status=status, skip=skip, limit=20)
            paginated_data = telescopes[skip:skip+20] if skip < len(telescopes) else []
            RedisCache.set("telescopes", key, paginated_data, ttl=CACHE_TTL_MEDIUM)
        
        logger.info(f"Cache Redis refreshed in background for status={status}")
    except Exception as e:
        logger.error(f"Error refreshing Redis cache: {str(e)}")

@router.get("/", response_model=List[TelescopeResponse])
async def list_telescopes(
    response: Response,
    background_tasks: BackgroundTasks,
    status: Optional[str] = Query(None, description="Filtrer par statut (ONLINE, OFFLINE, MAINTENANCE)"),
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter (pagination)"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"),
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Liste tous les télescopes disponibles avec pagination et support de cache Redis"""
    start_time = time.time()
    logger.info(f"Endpoint: GET /telescopes/ called with status={status}, skip={skip}, limit={limit}")
    
    # Génération de la clé de cache unique
    cache_key = generate_cache_key(status=status, skip=skip, limit=limit)
    
    # Déterminer le TTL en fonction du statut
    cache_ttl = CACHE_TTL_SHORT
    if status == "OFFLINE" or status == "MAINTENANCE":
        # Les données qui changent rarement peuvent être en cache plus longtemps
        cache_ttl = CACHE_TTL_LONG
    elif status == "ONLINE" or status is None:
        # Les données actives ont un TTL moyen
        cache_ttl = CACHE_TTL_MEDIUM
    
    # Vérifier si la réponse est en cache Redis
    cache_entry = RedisCache.get("telescopes", cache_key)
    
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
    telescope_service = TelescopeService(db)
    
    try:
        if status:
            from app.domain.value_objects.telescope_types import TelescopeStatus
            try:
                status_enum = TelescopeStatus[status.upper()]
                all_telescopes = await telescope_service.get_by_status(status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Statut invalide: {status}")
        else:
            all_telescopes = await telescope_service.get_active_telescopes()
            
        # Pagination des résultats
        telescopes = all_telescopes[skip:skip + limit] if skip < len(all_telescopes) else []
        
        # Mise à jour du cache Redis
        RedisCache.set("telescopes", cache_key, telescopes, ttl=cache_ttl)
        
        # Mettre en cache la liste complète également
        all_key = generate_cache_key(status=status)
        RedisCache.set("telescopes", all_key, all_telescopes, ttl=cache_ttl)
        
        # Récupérer l'ETag du cache
        updated_cache = RedisCache.get("telescopes", cache_key)
        if updated_cache and updated_cache.get("etag"):
            response.headers["ETag"] = updated_cache.get("etag")
        
        # Si cette requête a été lente, planifier des pré-calculs de cache en arrière-plan
        request_time = time.time() - start_time
        if request_time > 1.0:
            background_tasks.add_task(refresh_cache_in_background, db, status)
        
        logger.info(f"Request completed in {request_time:.3f}s")
        
        # Log une alerte si la requête est trop lente
        if request_time > 3.0:
            logger.warning(f"Slow endpoint detected: list_telescopes took {request_time:.3f}s")
        
        return telescopes
    
    except Exception as e:
        logger.error(f"Error in list_telescopes: {str(e)}")
        raise  # Pas de fallback au cache en cas d'erreur car nous utilisons Redis

@router.get("/{telescope_id}", response_model=TelescopeResponse)
async def get_telescope(
    telescope_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'un télescope avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour ce télescope
    cache_key = f"telescope_{telescope_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("telescope", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for telescope {telescope_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for telescope {telescope_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    telescope_service = TelescopeService(db)
    telescope = await telescope_service.get_telescope(telescope_id)
    
    if not telescope:
        raise HTTPException(status_code=404, detail="Télescope non trouvé")
    
    # Mise en cache Redis
    RedisCache.set("telescope", cache_key, telescope, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("telescope", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Telescope {telescope_id} fetched in {time.time() - start_time:.3f}s")
    return telescope

@router.get("/{telescope_id}/filters", response_model=List[FilterResponse])
async def get_telescope_filters(
    telescope_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les filtres disponibles pour un télescope avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour les filtres de ce télescope
    cache_key = f"telescope_filters_{telescope_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("filters", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for filters of telescope {telescope_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for filters of telescope {telescope_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    telescope_service = TelescopeService(db)
    filters = await telescope_service.get_telescope_filters(telescope_id)
    
    if not filters:
        raise HTTPException(status_code=404, detail="Filtres non trouvés ou télescope inexistant")
    
    # Conversion en objets Pydantic pour éviter la sérialisation des relations circulaires
    filter_responses = []
    for filter in filters:
        filter_response = FilterResponse.model_validate(filter)
        filter_response.telescope_name = filter.telescope_name
        filter_responses.append(filter_response)
    
    # Mise en cache Redis
    RedisCache.set("filters", cache_key, filter_responses, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("filters", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Filters for telescope {telescope_id} fetched in {time.time() - start_time:.3f}s")
    return filter_responses

@router.get("/{telescope_id}/presets", response_model=List[PresetResponse])
async def get_telescope_presets(
    telescope_id: UUID,
    response: Response,
    if_none_match: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Récupère les presets disponibles pour un télescope avec support de cache Redis"""
    start_time = time.time()
    
    # Clé de cache pour les presets de ce télescope
    cache_key = f"telescope_presets_{telescope_id}"
    
    # Vérifier le cache Redis
    cache_entry = RedisCache.get("presets", cache_key)
    
    # ETag et cache validation
    if cache_entry and cache_entry.get("etag") and cache_entry.get("etag") == if_none_match:
        logger.info(f"Redis cache hit with ETag for presets of telescope {telescope_id}")
        return Response(status_code=HTTP_304_NOT_MODIFIED)
    
    if cache_entry:
        logger.info(f"Redis cache hit for presets of telescope {telescope_id}")
        response.headers["ETag"] = cache_entry.get("etag")
        return cache_entry.get("data")
    
    # Requête à la DB si pas en cache
    telescope_service = TelescopeService(db)
    presets = await telescope_service.get_telescope_presets(telescope_id)
    
    if not presets:
        raise HTTPException(status_code=404, detail="Presets non trouvés ou télescope inexistant")
    
    # Conversion en objets Pydantic pour éviter la sérialisation des relations circulaires
    preset_responses = []
    for preset in presets:
        preset_response = PresetResponse.model_validate(preset)
        preset_responses.append(preset_response)
    
    # Mise en cache Redis
    RedisCache.set("presets", cache_key, preset_responses, ttl=CACHE_TTL_MEDIUM)
    
    # Récupérer l'ETag du cache
    updated_cache = RedisCache.get("presets", cache_key)
    if updated_cache and updated_cache.get("etag"):
        response.headers["ETag"] = updated_cache.get("etag")
    
    logger.info(f"Presets for telescope {telescope_id} fetched in {time.time() - start_time:.3f}s")
    return preset_responses
