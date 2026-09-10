"""
Execution trace recorder.
Records each pipeline step's status and timing to the SQLite database.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import TraceStep

PIPELINE_STEPS = [
    (0, "FILE_VALIDATION",       "File Detection & Basic Validation"),
    (1, "QUERY_INTERPRETATION",  "Understanding Your Request"),
    (2, "COMPATIBILITY_CHECK",   "Checking Image Compatibility"),
    (3, "MODEL_SELECTION",       "Selecting AI Specialist"),
    (4, "MODEL_EXECUTION",       "Running AI Analysis"),
    (5, "FUSION",                "Fusing Results"),
    (6, "CONFIDENCE_ESTIMATION", "Estimating Confidence"),
    (7, "EVIDENCE_GENERATION",   "Generating Evidence"),
    (8, "REPORT_ASSEMBLY",       "Assembling Execution Trace & Report"),
]


def init_trace(db: Session, job_id: str) -> None:
    """Create all 9 trace steps in 'pending' state for a job."""
    for idx, key, name in PIPELINE_STEPS:
        step = TraceStep(
            job_id=job_id,
            step_index=idx,
            step_name=name,
            status="pending",
        )
        db.add(step)
    db.commit()


def start_step(db: Session, job_id: str, step_index: int) -> None:
    step = db.query(TraceStep).filter_by(job_id=job_id, step_index=step_index).first()
    if step:
        step.status = "running"
        step.started_at = datetime.utcnow()
        db.commit()


def complete_step(db: Session, job_id: str, step_index: int,
                  message: Optional[str] = None, detail: Optional[dict] = None) -> None:
    step = db.query(TraceStep).filter_by(job_id=job_id, step_index=step_index).first()
    if step:
        step.status = "completed"
        step.completed_at = datetime.utcnow()
        if message:
            step.message = message
        if detail:
            step.detail = detail
        db.commit()


def error_step(db: Session, job_id: str, step_index: int, message: str) -> None:
    step = db.query(TraceStep).filter_by(job_id=job_id, step_index=step_index).first()
    if step:
        step.status = "error"
        step.completed_at = datetime.utcnow()
        step.message = message
        db.commit()


def skip_remaining_steps(db: Session, job_id: str, from_step: int) -> None:
    steps = db.query(TraceStep).filter(
        TraceStep.job_id == job_id,
        TraceStep.step_index >= from_step
    ).all()
    for step in steps:
        if step.status == "pending":
            step.status = "skipped"
    db.commit()


def get_trace(db: Session, job_id: str) -> list[dict]:
    steps = db.query(TraceStep).filter_by(job_id=job_id).order_by(TraceStep.step_index).all()
    return [
        {
            "step_index": s.step_index,
            "step_name": s.step_name,
            "status": s.status,
            "message": s.message,
            "detail": s.detail,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        for s in steps
    ]
