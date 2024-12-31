# app/api/v1/router.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.api.v1.endpoints import telescopes, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    telescopes.router,
    prefix="/telescopes",
    tags=["telescopes"],
    dependencies=[Depends(get_current_user)]  # Protège tous les endpoints telescopes
)
