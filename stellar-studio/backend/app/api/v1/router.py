# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import telescopes

api_router = APIRouter()
api_router.include_router(telescopes.router, prefix="/telescopes", tags=["telescopes"])
