"""GET /api/report/{job_id} — generate and stream a PDF report via ReportLab."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime

from app.db.database import get_db
from app.db.models import Job
from app.core.trace import get_trace

router = APIRouter()


def _generate_pdf(job: Job, trace_steps: list[dict]) -> BytesIO:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise HTTPException(status_code=500, detail="ReportLab not installed. Cannot generate PDF.")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=18, spaceAfter=6)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=12, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, spaceAfter=3)
    mono_style = ParagraphStyle("Mono", parent=styles["Code"], fontSize=8, spaceAfter=2)
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=8,
                                  textColor=colors.grey, spaceAfter=2)

    story = []

    # Header
    story.append(Paragraph("SatQuery AI — Analysis Report", title_style))
    story.append(Paragraph(f"Job ID: {job.id}", label_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", label_style))
    story.append(Paragraph(f"Mode: {job.mode.upper()}", label_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3*cm))

    # Query
    story.append(Paragraph("Query", heading_style))
    story.append(Paragraph(job.query_text or "(none)", body_style))
    story.append(Spacer(1, 0.3*cm))

    # Compatibility
    if job.compatibility_status:
        story.append(Paragraph("Compatibility Check", heading_style))
        story.append(Paragraph(f"Status: {job.compatibility_status.upper()}", body_style))
        if job.compatibility_message:
            story.append(Paragraph(job.compatibility_message, body_style))
        if job.gsd_limitation_note:
            story.append(Paragraph(f"Resolution note: {job.gsd_limitation_note}", label_style))
        story.append(Spacer(1, 0.3*cm))

    # Results
    result = job.result or {}
    subtasks = result.get("subtasks", [])
    if subtasks:
        story.append(Paragraph("Analysis Results", heading_style))
        for i, sub in enumerate(subtasks, 1):
            story.append(Paragraph(f"Subtask {i}: {sub.get('task_type', '')}", body_style))
            story.append(Paragraph(f"Query: {sub.get('query_fragment', '')}", label_style))
            if sub.get("supported"):
                story.append(Paragraph(f"Answer: {sub.get('answer', '')}", body_style))
            else:
                story.append(Paragraph(f"⚠ {sub.get('limitation_message', 'Subtask not supported.')}", label_style))
            if sub.get("evidence"):
                for ev in sub["evidence"]:
                    story.append(Paragraph(
                        f"Evidence [{ev.get('type')}]: {ev.get('label', '')} — provenance: {ev.get('provenance')}",
                        label_style
                    ))
            story.append(Spacer(1, 0.2*cm))

    # Confidence
    hc = result.get("heuristic_confidence")
    if hc:
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("Confidence Breakdown", heading_style))
        story.append(Paragraph(hc.get("label", ""), label_style))
        conf_data = [
            ["Component", "Weight", "Value"],
            ["Query Interpretation", "0.25", f"{hc.get('query_confidence', 0):.3f}"],
            ["Compatibility Score", "0.20", f"{hc.get('compatibility_score', 0):.3f}"],
            ["Model Confidence", "0.35", str(hc.get('model_confidence')) if hc.get('model_confidence') is not None else "N/A"],
            ["Evidence Consistency", "0.20", str(hc.get('evidence_consistency')) if hc.get('evidence_consistency') is not None else "N/A"],
            ["Final (Heuristic)", "—", f"{hc.get('final_confidence', 0):.3f}" + (" [CAPPED]" if hc.get('capped') else "")],
        ]
        t = Table(conf_data, colWidths=[8*cm, 3*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2a40")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8ff")]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    # Model Info
    model_info = result.get("model_info")
    if model_info:
        story.append(Paragraph("Model Information", heading_style))
        story.append(Paragraph(f"Name: {model_info.get('name')}", body_style))
        story.append(Paragraph(f"Encoder: {model_info.get('encoder')}", body_style))
        story.append(Paragraph(f"Training Status: {model_info.get('training_status')}", body_style))
        story.append(Paragraph(f"Mode: {model_info.get('model_mode')}", body_style))
        story.append(Paragraph(f"Inference: {model_info.get('inference_provenance')}", label_style))
        story.append(Spacer(1, 0.3*cm))

    # Execution Trace
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Execution Trace", heading_style))
    for step in trace_steps:
        started = step.get("started_at", "")[:19] if step.get("started_at") else "—"
        completed = step.get("completed_at", "")[:19] if step.get("completed_at") else "—"
        status_icon = {"completed": "✓", "error": "✗", "skipped": "—", "running": "⟳", "pending": "·"}.get(step["status"], "?")
        story.append(Paragraph(
            f"{status_icon} [{step['step_index']}] {step['step_name']} — {step['status']} | {started} → {completed}",
            mono_style
        ))
        if step.get("message"):
            story.append(Paragraph(f"   {step['message']}", label_style))

    doc.build(story)
    buf.seek(0)
    return buf


@router.get("/report/{job_id}")
def download_report(job_id: str, db: Session = Depends(get_db)):
    """Generate and stream a PDF analysis report for the given job."""
    job = db.query(Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    if job.status not in ("completed", "needs_clarification", "incompatible", "error"):
        raise HTTPException(status_code=409, detail="Job is still processing. Report not yet available.")

    trace_steps = get_trace(db, job_id)
    pdf_buf = _generate_pdf(job, trace_steps)

    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=satquery_report_{job_id[:8]}.pdf"}
    )
