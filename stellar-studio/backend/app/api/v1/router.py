# app/api/v1/router.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.api.v1.endpoints import auth, telescopes, targets, presets, tasks, health
from app.api.v1.endpoints.ws.connection import router as ws_router

api_router = APIRouter()

# Routes publiques
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Routes protégées (tout le reste)
protected_routes = [
    (telescopes.router, "telescopes"),
    (targets.router, "targets"),
    (presets.router, "presets"),
    (tasks.router, "tasks"),
    (ws_router, "ws")
]

for router, tag in protected_routes:
    api_router.include_router(
        router,
        prefix=f"/{tag}",
        tags=[tag],
        dependencies=[Depends(get_current_user)]
    )
