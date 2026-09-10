"""GET /api/models — list registered specialist models with capabilities."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.registry import registry

router = APIRouter()


@router.get("/models")
def list_models():
    """Return all registered specialist models with their declared capabilities and encoder status."""
    return JSONResponse({"models": registry.list_all()})
