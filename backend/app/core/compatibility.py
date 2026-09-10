"""
Task-aware compatibility checker.
Validates uploaded files against the task requirements (GSD, modality, co-registration).
Returns: compatible | warning | incompatible — with explicit reason strings.
"""
from dataclasses import dataclass
from typing import Optional
from app.core.validator import FileMetadata, GSD_THRESHOLDS


@dataclass
class CompatibilityResult:
    status: str            # "compatible" | "warning" | "incompatible"
    message: str           # Plain-language message for the user (never a stack trace)
    gsd_limitation_note: Optional[str]
    compatibility_score: float   # 1.0 | 0.6 | 0.0  — used in confidence formula


# GSD requirements per task (min acceptable GSD in meters — lower = finer resolution)
TASK_GSD_REQUIREMENTS: dict[str, float] = {
    "rs-vqa-binary": 100.0,
    "rs-vqa-mcq": 100.0,
    "captioning": 100.0,
    "change-vqa": 30.0,
    "grounding": 30.0,           # region-level grounding
    "grounding_object": 5.0,     # individual-object grounding (upgraded by controller)
    "fusion": 30.0,
}

# Expected modalities per task
TASK_MODALITY_REQUIREMENTS: dict[str, list[str]] = {
    "rs-vqa-binary": ["optical", "sar", "unknown"],
    "rs-vqa-mcq": ["optical", "sar", "unknown"],
    "captioning": ["optical", "unknown"],
    "change-vqa": ["optical", "unknown"],
    "grounding": ["optical", "unknown"],
    "fusion": ["optical", "sar"],
}


def _check_single_image(file: FileMetadata, task_type: str) -> CompatibilityResult:
    """Validate a single-image task."""
    gsd = file.gsd_meters
    required_gsd = TASK_GSD_REQUIREMENTS.get(task_type, 100.0)

    # GSD check (only if GSD is known)
    if gsd is not None:
        if gsd > required_gsd * 2:
            return CompatibilityResult(
                status="incompatible",
                message=(
                    f"The image spatial resolution ({gsd:.0f} m/px) is too coarse for "
                    f"'{task_type}' analysis, which requires at least {required_gsd:.0f} m/px resolution."
                ),
                gsd_limitation_note=f"Image GSD {gsd:.0f} m/px; required ≤{required_gsd:.0f} m/px.",
                compatibility_score=0.0
            )
        elif gsd > required_gsd:
            return CompatibilityResult(
                status="warning",
                message=(
                    f"Image resolution ({gsd:.0f} m/px) is marginal for this task "
                    f"(recommended ≤{required_gsd:.0f} m/px). Results may be less reliable."
                ),
                gsd_limitation_note=f"Resolution marginal: {gsd:.0f} m/px vs {required_gsd:.0f} m/px recommended.",
                compatibility_score=0.6
            )

    # Modality check
    allowed = TASK_MODALITY_REQUIREMENTS.get(task_type, ["optical", "sar", "unknown"])
    if file.modality not in allowed and file.modality != "unknown":
        return CompatibilityResult(
            status="warning",
            message=f"This task works best with {'/'.join(allowed)} imagery; received {file.modality}.",
            gsd_limitation_note=None,
            compatibility_score=0.6
        )

    return CompatibilityResult(
        status="compatible",
        message="Image is compatible with the requested task.",
        gsd_limitation_note=None,
        compatibility_score=1.0
    )


def _check_bitemporal_pair(file_t1: FileMetadata, file_t2: FileMetadata, task_type: str) -> CompatibilityResult:
    """Validate a bi-temporal pair for co-registration and consistency."""
    warnings = []

    # CRS mismatch
    if file_t1.crs and file_t2.crs and file_t1.crs != file_t2.crs:
        return CompatibilityResult(
            status="incompatible",
            message=(
                "These images cannot be compared because their coordinate reference systems "
                "do not match (CRS mismatch). Please use images in the same CRS."
            ),
            gsd_limitation_note=f"CRS mismatch: {file_t1.crs} vs {file_t2.crs}",
            compatibility_score=0.0
        )

    # Band count mismatch
    if file_t1.band_count != file_t2.band_count:
        return CompatibilityResult(
            status="incompatible",
            message=(
                "These images cannot be compared because they have different numbers of spectral bands. "
                f"Image 1 has {file_t1.band_count} bands; Image 2 has {file_t2.band_count} bands."
            ),
            gsd_limitation_note=None,
            compatibility_score=0.0
        )

    # Resolution mismatch (warning if > 2x difference)
    if file_t1.gsd_meters and file_t2.gsd_meters:
        ratio = max(file_t1.gsd_meters, file_t2.gsd_meters) / min(file_t1.gsd_meters, file_t2.gsd_meters)
        if ratio > 3.0:
            return CompatibilityResult(
                status="incompatible",
                message=(
                    "These images cannot be compared because their spatial resolutions differ too much. "
                    f"({file_t1.gsd_meters:.0f} m/px vs {file_t2.gsd_meters:.0f} m/px)"
                ),
                gsd_limitation_note=f"Resolution mismatch: {file_t1.gsd_meters:.0f} m/px vs {file_t2.gsd_meters:.0f} m/px",
                compatibility_score=0.0
            )
        elif ratio > 1.5:
            warnings.append(
                f"Resolution mismatch: {file_t1.gsd_meters:.0f} m/px vs {file_t2.gsd_meters:.0f} m/px"
            )

    # Size mismatch (warning)
    if file_t1.width_px > 0 and file_t2.width_px > 0:
        size_diff_pct = abs(file_t1.width_px - file_t2.width_px) / max(file_t1.width_px, file_t2.width_px)
        if size_diff_pct > 0.2:
            warnings.append(f"Image dimensions differ significantly ({file_t1.width_px}×{file_t1.height_px} vs {file_t2.width_px}×{file_t2.height_px})")

    # GSD check for the task
    ref_gsd = file_t1.gsd_meters or file_t2.gsd_meters
    required_gsd = TASK_GSD_REQUIREMENTS.get(task_type, 30.0)
    if ref_gsd and ref_gsd > required_gsd * 2:
        return CompatibilityResult(
            status="incompatible",
            message=f"Image resolution ({ref_gsd:.0f} m/px) is insufficient for change analysis (requires ≤{required_gsd:.0f} m/px).",
            gsd_limitation_note=f"Image GSD {ref_gsd:.0f} m/px; required ≤{required_gsd:.0f} m/px.",
            compatibility_score=0.0
        )

    if warnings:
        return CompatibilityResult(
            status="warning",
            message="Images are usable but have minor inconsistencies: " + "; ".join(warnings),
            gsd_limitation_note="; ".join(warnings) if warnings else None,
            compatibility_score=0.6
        )

    return CompatibilityResult(
        status="compatible",
        message="Bi-temporal image pair is compatible for change analysis.",
        gsd_limitation_note=None,
        compatibility_score=1.0
    )


def check_compatibility(
    files: list[FileMetadata],
    task_type: str,
    temporal_pair: bool = False
) -> CompatibilityResult:
    """
    Main compatibility check entry point.
    Called AFTER query interpretation — task_type must be known.
    Enforces temporal integrity: change-vqa requires exactly two observations.
    """
    if not files:
        return CompatibilityResult(
            status="incompatible",
            message="No valid files were provided for analysis.",
            gsd_limitation_note=None,
            compatibility_score=0.0
        )

    requires_temporal = (task_type == "change-vqa" or temporal_pair)
    if requires_temporal:
        if len(files) < 2:
            return CompatibilityResult(
                status="incompatible",
                message="Change analysis requires two temporal observations (e.g. before and after images). Only one image was uploaded.",
                gsd_limitation_note=None,
                compatibility_score=0.0
            )
        return _check_bitemporal_pair(files[0], files[1], task_type)

    return _check_single_image(files[0], task_type)
