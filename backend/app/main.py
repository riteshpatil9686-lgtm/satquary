"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.db.database import init_db
from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise SQLite database."""
    init_db()
    os.makedirs("uploads", exist_ok=True)
    yield


app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Multimodal Remote Sensing",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "SatQuery AI",
        "version": "2.0.0",
        "mode": settings.MODE,
        "docs": "/docs",
    }
