"""POST /api/analyze — run the full 9-step analysis pipeline."""
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import Job, UploadedFile
from app.core.interpreter import interpret_query
from app.core.compatibility import check_compatibility
from app.core.validator import FileMetadata
from app.core.controller import route_and_execute
from app.core import trace as tracer

router = APIRouter()


class AnalyzeRequest(BaseModel):
    file_tokens: list[str]          # 1 or 2 file tokens from /api/upload
    query: str
    aoi_bounds: Optional[dict] = None  # {north, south, east, west}


def _get_file_metadata(db: Session, token: str) -> Optional[FileMetadata]:
    record = db.query(UploadedFile).filter_by(token=token).first()
    if not record:
        return None
    return FileMetadata(
        token=record.token,
        original_filename=record.original_filename,
        saved_path=record.saved_path,
        file_size_bytes=record.file_size_bytes or 0,
        modality=record.modality or "unknown",
        gsd_meters=record.gsd_meters,
        band_count=record.band_count or 0,
        width_px=record.width_px or 0,
        height_px=record.height_px or 0,
        crs=record.crs,
        valid=True,
        validation_error=None,
    )


def _run_pipeline(job_id: str):
    """Background task — executes the full 9-step pipeline and updates the job record."""
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # Step 1: File validation (already done in upload; retrieve metadata)
        tracer.start_step(db, job_id, 0)
        file_metas = []
        for token in (job.file_tokens or []):
            meta = _get_file_metadata(db, token)
            if not meta:
                tracer.error_step(db, job_id, 0, f"File token '{token}' not found in database.")
                job.status = "error"
                job.error_message = f"Uploaded file not found for token '{token}'. Please re-upload."
                db.commit()
                tracer.skip_remaining_steps(db, job_id, 1)
                return
            file_metas.append(meta)
        tracer.complete_step(db, job_id, 0,
            message=f"{len(file_metas)} file(s) loaded and validated.",
            detail={"files": [{"token": m.token, "gsd_meters": m.gsd_meters, "modality": m.modality} for m in file_metas]}
        )

        # Step 2: Query interpretation
        tracer.start_step(db, job_id, 1)
        interp = interpret_query(job.query_text or "", threshold=settings.QUERY_CONFIDENCE_THRESHOLD)
        tracer.complete_step(db, job_id, 1,
            message=f"Task: {interp.primary_task} | Confidence: {interp.confidence:.2f}",
            detail={
                "primary_task": interp.primary_task,
                "confidence": interp.confidence,
                "temporal_intent": interp.temporal_intent,
                "multi_part": interp.multi_part,
                "subtask_count": len(interp.subtasks),
            }
        )

        # Handle low confidence
        if interp.needs_clarification:
            tracer.skip_remaining_steps(db, job_id, 2)
            job.status = "needs_clarification"
            job.clarification_candidates = interp.clarification_candidates
            db.commit()
            return

        # Step 3: Compatibility check
        tracer.start_step(db, job_id, 2)
        has_temporal_intent = (interp.primary_task == "change-vqa" or interp.temporal_intent)
        compat = check_compatibility(file_metas, interp.primary_task, temporal_pair=has_temporal_intent)
        tracer.complete_step(db, job_id, 2,
            message=f"Compatibility: {compat.status} | Score: {compat.compatibility_score}",
            detail={"status": compat.status, "message": compat.message, "gsd_note": compat.gsd_limitation_note}
        )

        job.compatibility_status = compat.status
        job.compatibility_message = compat.message
        job.gsd_limitation_note = compat.gsd_limitation_note
        db.commit()

        if compat.status == "incompatible":
            job.status = "incompatible"
            job.error_message = compat.message
            db.commit()
            tracer.skip_remaining_steps(db, job_id, 3)
            return

        # Steps 4–9: Controller handles model selection, inference, confidence, evidence
        temporal_pair = has_temporal_intent and len(file_metas) >= 2
        image_paths = [m.saved_path for m in file_metas]
        subtasks_dicts = [
            {"subtask_id": s.subtask_id, "task_type": s.task_type, "query_fragment": s.query_fragment}
            for s in interp.subtasks
        ]

        result = route_and_execute(
            db=db,
            job_id=job_id,
            image_paths=image_paths,
            query=job.query_text or "",
            primary_task=interp.primary_task,
            subtasks=subtasks_dicts,
            query_confidence=interp.confidence,
            compatibility_score=compat.compatibility_score,
            compatibility_warning=(compat.status == "warning"),
            warning_reason=compat.gsd_limitation_note or compat.message,
            temporal_pair=temporal_pair,
            file_metas=file_metas,
        )

        if result.get("status") == "error":
            job.status = "error"
            job.error_message = result.get("error", "Unknown error during analysis.")
        else:
            result["compatibility_status"] = compat.status
            result["compatibility_message"] = compat.message
            result["gsd_limitation_note"] = compat.gsd_limitation_note
            result["job_id"] = job_id
            job.result = result
            job.task_type = interp.primary_task
            job.temporal_pair = temporal_pair
            job.status = "completed"

        db.commit()

    except Exception as e:
        try:
            job = db.query(Job).filter_by(id=job_id).first()
            if job:
                job.status = "error"
                # Never expose stack trace to user-facing fields
                job.error_message = "An internal error occurred during analysis. Please try again."
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not req.file_tokens:
        raise HTTPException(status_code=422, detail="At least one file_token is required.")
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="Query text cannot be empty.")

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        status="pending",
        mode=settings.MODE,
        query_text=req.query.strip(),
        file_tokens=req.file_tokens,
        aoi_bounds=req.aoi_bounds,
        temporal_pair=len(req.file_tokens) >= 2,
    )
    db.add(job)
    db.commit()

    tracer.init_trace(db, job_id)
    background_tasks.add_task(_run_pipeline, job_id)

    return JSONResponse({"job_id": job_id, "status": "pending"})
