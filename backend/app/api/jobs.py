"""GET /api/jobs/{job_id} and GET /api/results/{job_id}"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Job
from app.core.trace import get_trace

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Return job status and execution trace steps for the processing overlay poller."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    trace_steps = get_trace(db, job_id)
    tokens = job.file_tokens or []
    preview_url = f"/api/files/{tokens[0]}/preview" if tokens else None
    return JSONResponse({
        "job_id": job_id,
        "status": job.status,
        "mode": job.mode,
        "query_text": job.query_text,
        "task_type": job.task_type,
        "compatibility_status": job.compatibility_status,
        "compatibility_message": job.compatibility_message,
        "gsd_limitation_note": job.gsd_limitation_note,
        "error_message": job.error_message,
        "clarification_candidates": job.clarification_candidates,
        "temporal_pair": job.temporal_pair,
        "file_tokens": tokens,
        "file_url": preview_url,
        "preview_url": preview_url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "trace_steps": trace_steps,
    })


@router.get("/results/{job_id}")
def get_results(job_id: str, db: Session = Depends(get_db)):
    """Return full analysis result once job is completed."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    tokens = job.file_tokens or []
    preview_url = f"/api/files/{tokens[0]}/preview" if tokens else None
    if job.status == "pending" or job.status == "processing":
        return JSONResponse({"job_id": job_id, "status": job.status, "result": None, "preview_url": preview_url})
    if job.status in ("needs_clarification", "incompatible", "error"):
        return JSONResponse({
            "job_id": job_id,
            "status": job.status,
            "error_message": job.error_message,
            "clarification_candidates": job.clarification_candidates,
            "compatibility_message": job.compatibility_message,
            "file_tokens": tokens,
            "file_url": preview_url,
            "preview_url": preview_url,
            "result": None,
        })
    trace_steps = get_trace(db, job_id)
    result = job.result or {}
    result["trace_steps"] = trace_steps
    result["file_tokens"] = tokens
    result["file_url"] = preview_url
    result["preview_url"] = preview_url
    result["preview_urls"] = [f"/api/files/{t}/preview" for t in tokens]
    return JSONResponse(result)
