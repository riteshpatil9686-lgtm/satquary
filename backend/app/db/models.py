import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, Integer, JSON
from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default="pending")  # pending | processing | completed | error | needs_clarification | incompatible
    mode = Column(String, default="demo")       # demo | real
    query_text = Column(Text, nullable=True)
    task_type = Column(String, nullable=True)
    file_tokens = Column(JSON, default=list)    # list of uploaded file token dicts
    aoi_bounds = Column(JSON, nullable=True)    # {north, south, east, west}
    temporal_pair = Column(Boolean, default=False)
    compatibility_status = Column(String, nullable=True)  # compatible | warning | incompatible
    compatibility_message = Column(Text, nullable=True)
    gsd_limitation_note = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    clarification_candidates = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)        # full AnalysisResult JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TraceStep(Base):
    __tablename__ = "trace_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | running | completed | error | skipped
    message = Column(Text, nullable=True)
    detail = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    token = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    saved_path = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    modality = Column(String, nullable=True)    # optical | sar | unknown
    gsd_meters = Column(Float, nullable=True)
    band_count = Column(Integer, nullable=True)
    width_px = Column(Integer, nullable=True)
    height_px = Column(Integer, nullable=True)
    crs = Column(String, nullable=True)
    temporal_label = Column(String, nullable=True)  # t1 | t2 | single
    created_at = Column(DateTime, default=datetime.utcnow)
