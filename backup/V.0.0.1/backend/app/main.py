# app/main.py
from fastapi import FastAPI
from app.api.v1.router import router as api_v1_router

app = FastAPI(title="Stellar Studio API")

app.include_router(api_v1_router, prefix="/api/v1")
