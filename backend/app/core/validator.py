"""
File validation and GSD/metadata extractor.
Uses rasterio (Path B manylinux wheel) and Pillow only — no raw osgeo.gdal calls.
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

try:
    import rasterio
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Supported file formats
SUPPORTED_FORMATS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}

# GSD thresholds for task compatibility (meters per pixel)
GSD_THRESHOLDS = {
    "scene_classification": 100.0,     # Coarse OK
    "rs-vqa-binary": 100.0,
    "rs-vqa-mcq": 100.0,
    "captioning": 100.0,
    "change-vqa": 30.0,                # Need at least moderate resolution
    "grounding_large_region": 30.0,    # Large region detection
    "grounding_object": 5.0,           # Individual object/building detection
    "fusion": 30.0,
    "counting_coarse": 10.0,           # Coarse counting (fields, forest patches)
    "counting_individual": 2.0,        # Individual small object counting (vehicles etc)
}


@dataclass
class FileMetadata:
    token: str
    original_filename: str
    saved_path: str
    file_size_bytes: int
    modality: str           # optical | sar | unknown
    gsd_meters: Optional[float]
    band_count: int
    width_px: int
    height_px: int
    crs: Optional[str]
    valid: bool
    validation_error: Optional[str]
    temporal_label: Optional[str] = None


def _guess_modality_from_bands(band_count: int, filename: str) -> str:
    """Heuristic modality guess from band count and filename."""
    fname_lower = filename.lower()
    if "sar" in fname_lower or "s1" in fname_lower or "sentinel1" in fname_lower:
        return "sar"
    if band_count == 1 or band_count == 2:
        return "sar"  # Likely VV/VH SAR
    if band_count in (3, 4, 12, 13):
        return "optical"
    return "unknown"


def _estimate_gsd_from_transform(transform, crs) -> Optional[float]:
    """Estimate GSD in meters from rasterio transform and CRS."""
    try:
        pixel_width = abs(transform.a)
        pixel_height = abs(transform.e)
        avg_pixel = (pixel_width + pixel_height) / 2.0
        # If CRS is geographic (degrees), rough conversion at mid-latitudes
        if crs and hasattr(crs, 'is_geographic') and crs.is_geographic:
            avg_pixel = avg_pixel * 111320  # degrees → meters approx
        return round(avg_pixel, 2) if avg_pixel > 0 else None
    except Exception:
        return None


def validate_and_save_file(file_bytes: bytes, original_filename: str) -> FileMetadata:
    """
    Validate uploaded file and save to disk.
    Returns FileMetadata with valid=False and validation_error set on failure.
    """
    token = str(uuid.uuid4())
    ext = Path(original_filename).suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        return FileMetadata(
            token=token, original_filename=original_filename, saved_path="",
            file_size_bytes=len(file_bytes), modality="unknown",
            gsd_meters=None, band_count=0, width_px=0, height_px=0,
            crs=None, valid=False,
            validation_error=f"Unsupported file format '{ext}'. Accepted: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Save file
    saved_path = UPLOAD_DIR / f"{token}{ext}"
    saved_path.write_bytes(file_bytes)

    # Try rasterio first (handles GeoTIFF with full metadata)
    if RASTERIO_AVAILABLE and ext in (".tif", ".tiff"):
        try:
            with rasterio.open(str(saved_path)) as ds:
                band_count = ds.count
                width_px = ds.width
                height_px = ds.height
                crs_str = str(ds.crs) if ds.crs else None
                gsd_meters = _estimate_gsd_from_transform(ds.transform, ds.crs)
                modality = _guess_modality_from_bands(band_count, original_filename)

                return FileMetadata(
                    token=token, original_filename=original_filename,
                    saved_path=str(saved_path),
                    file_size_bytes=len(file_bytes),
                    modality=modality, gsd_meters=gsd_meters,
                    band_count=band_count, width_px=width_px, height_px=height_px,
                    crs=crs_str, valid=True, validation_error=None
                )
        except Exception as e:
            saved_path.unlink(missing_ok=True)
            return FileMetadata(
                token=token, original_filename=original_filename, saved_path="",
                file_size_bytes=len(file_bytes), modality="unknown",
                gsd_meters=None, band_count=0, width_px=0, height_px=0,
                crs=None, valid=False, validation_error=f"Could not read raster file: {str(e)}"
            )

    # Fallback: Pillow for PNG/JPEG
    if PILLOW_AVAILABLE:
        try:
            img = PILImage.open(saved_path)
            img.verify()
            img = PILImage.open(saved_path)  # re-open after verify
            width_px, height_px = img.size
            band_count = len(img.getbands())
            modality = _guess_modality_from_bands(band_count, original_filename)
            return FileMetadata(
                token=token, original_filename=original_filename,
                saved_path=str(saved_path),
                file_size_bytes=len(file_bytes),
                modality=modality, gsd_meters=None,  # No GSD from PNG/JPEG
                band_count=band_count, width_px=width_px, height_px=height_px,
                crs=None, valid=True, validation_error=None
            )
        except Exception as e:
            saved_path.unlink(missing_ok=True)
            return FileMetadata(
                token=token, original_filename=original_filename, saved_path="",
                file_size_bytes=len(file_bytes), modality="unknown",
                gsd_meters=None, band_count=0, width_px=0, height_px=0,
                crs=None, valid=False, validation_error=f"Could not read image: {str(e)}"
            )

    return FileMetadata(
        token=token, original_filename=original_filename, saved_path="",
        file_size_bytes=len(file_bytes), modality="unknown",
        gsd_meters=None, band_count=0, width_px=0, height_px=0,
        crs=None, valid=False, validation_error="No image processing library available."
    )
