# app/api/v1/router.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.api.v1.endpoints import auth, telescopes, telescope_management

api_router = APIRouter()

# Routes d'authentification
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Routes publiques des télescopes (avec auth requise)
api_router.include_router(
    telescopes.router,
    prefix="/telescopes",
    tags=["telescopes"],
    dependencies=[Depends(get_current_user)]
)

# Routes d'administration des télescopes
api_router.include_router(
    telescope_management.router,
    prefix="/admin/telescopes",
    tags=["telescope-management"],
    dependencies=[Depends(get_current_user)]
)
