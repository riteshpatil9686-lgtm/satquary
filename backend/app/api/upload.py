"""POST /api/upload — validate and save uploaded satellite image files."""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import UploadedFile
from app.core.validator import validate_and_save_file

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    temporal_label: str = "single",   # "single" | "t1" | "t2"
    db: Session = Depends(get_db),
):
    """
    Accept a satellite image file, validate it, extract metadata, and return a file token.
    The token is used in subsequent /analyze requests.
    """
    # Size check
    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed: {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    meta = validate_and_save_file(file_bytes, file.filename or "upload")

    if not meta.valid:
        raise HTTPException(status_code=422, detail=meta.validation_error)

    # Persist to DB
    record = UploadedFile(
        token=meta.token,
        original_filename=meta.original_filename,
        saved_path=meta.saved_path,
        file_size_bytes=meta.file_size_bytes,
        modality=meta.modality,
        gsd_meters=meta.gsd_meters,
        band_count=meta.band_count,
        width_px=meta.width_px,
        height_px=meta.height_px,
        crs=meta.crs,
        temporal_label=temporal_label,
    )
    db.add(record)
    db.commit()

    return JSONResponse({
        "file_token": meta.token,
        "original_filename": meta.original_filename,
        "modality": meta.modality,
        "gsd_meters": meta.gsd_meters,
        "band_count": meta.band_count,
        "width_px": meta.width_px,
        "height_px": meta.height_px,
        "crs": meta.crs,
        "temporal_label": temporal_label,
        "file_size_mb": round(size_mb, 2),
    })


@router.get("/files/{token}/preview")
@router.get("/preview/{token}")
def get_file_preview(token: str, db: Session = Depends(get_db)):
    """
    Return a browser-renderable raster representation (PNG/JPEG) of the uploaded satellite image.
    Converts GeoTIFF/TIFF to browser-compatible PNG in memory on the fly.
    """
    import io
    from pathlib import Path
    from fastapi.responses import Response, FileResponse
    from PIL import Image as PILImage

    record = db.query(UploadedFile).filter_by(token=token).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"File token '{token}' not found.")

    saved_path = Path(record.saved_path)
    if not saved_path.exists():
        # Fallback to fixtures directory if file was generated or referenced there
        fixture_path = Path("fixtures") / record.original_filename
        if fixture_path.exists():
            saved_path = fixture_path
        else:
            raise HTTPException(status_code=404, detail=f"Image file not found on server disk.")

    ext = saved_path.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else f"image/{ext.lstrip('.')}"
        return FileResponse(str(saved_path), media_type=media_type)

    # Convert TIFF/GeoTIFF to PNG for browser display
    try:
        with PILImage.open(str(saved_path)) as img:
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate image preview: {str(e)}")

