# app/api/v1/router.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.api.v1.endpoints import auth, telescopes, telescope_management, objects, observations, tasks

api_router = APIRouter()

# Routes d'authentification
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    telescopes.router,
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

api_router.include_router(
    observations.router,
    prefix="/observations",
    tags=["observations"]
)
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["tasks"]
)
api_router.include_router(
    objects.router,
    prefix="/objects",
    tags=["objects"]
)
