# app/api/v1/router.py
from fastapi import APIRouter
from .endpoints import telescopes

router = APIRouter()
router.include_router(telescopes.router, tags=["telescopes"])
