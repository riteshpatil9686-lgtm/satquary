"""POST /api/clarify/{job_id} — submit user's chosen task when query confidence was low."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Job
from app.core import trace as tracer

router = APIRouter()


class ClarifyRequest(BaseModel):
    chosen_task: str   # task type chosen by the user from clarification_candidates


@router.post("/clarify/{job_id}")
async def clarify(
    job_id: str,
    req: ClarifyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Accept user's task choice and re-run the pipeline with the confirmed task."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status != "needs_clarification":
        raise HTTPException(
            status_code=409,
            detail=f"Job is in status '{job.status}', not 'needs_clarification'."
        )

    # Validate chosen task is one of the candidates
    candidates = [c["task"] for c in (job.clarification_candidates or [])]
    if req.chosen_task not in candidates:
        raise HTTPException(
            status_code=422,
            detail=f"'{req.chosen_task}' is not a valid clarification candidate. Choose from: {candidates}"
        )

    # Reset job and re-run pipeline with forced task
    job.status = "pending"
    job.query_text = f"[task:{req.chosen_task}] {job.query_text}"
    job.clarification_candidates = None
    db.commit()
    tracer.init_trace(db, job_id)

    from app.api.analyze import _run_pipeline
    background_tasks.add_task(_run_pipeline, job_id)

    return JSONResponse({"job_id": job_id, "status": "pending", "chosen_task": req.chosen_task})
