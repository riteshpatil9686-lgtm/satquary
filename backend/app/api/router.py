"""Aggregated API router."""
from fastapi import APIRouter
from app.api import upload, analyze, jobs, clarify, models_api, report, health

router = APIRouter(prefix="/api")
router.include_router(upload.router)
router.include_router(analyze.router)
router.include_router(jobs.router)
router.include_router(clarify.router)
router.include_router(models_api.router)
router.include_router(report.router)
router.include_router(health.router)
