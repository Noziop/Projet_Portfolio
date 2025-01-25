# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.monitoring import setup_monitoring
from app.services.minio_service import init_minio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Setup monitoring avant d'inclure les routes
instrumentator = setup_monitoring(app)

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
    # Debug : afficher toutes les routes
    routes = [{"path": route.path, "name": route.name} for route in app.routes]
    print("Routes disponibles:", routes)
    init_minio()

