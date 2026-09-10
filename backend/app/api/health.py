"""GET /api/health — system health check."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check database connectivity, model registry, and device."""
    # DB check
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Device check
    try:
        import torch
        if settings.DEVICE == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = settings.DEVICE
        torch_status = "ok"
    except ImportError:
        device = "cpu"
        torch_status = "pytorch not installed"

    return JSONResponse({
        "status": "healthy" if db_status == "ok" else "degraded",
        "mode": settings.MODE,
        "device": device,
        "database": db_status,
        "pytorch": torch_status,
    })
