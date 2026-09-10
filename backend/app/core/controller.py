"""
Agentic controller / task router.
Routes to the correct specialist model and executes the full inference pipeline.
Orchestrates steps 4–8 of the canonical pipeline.
Enforces strict input- and query-aware matching, evidence provenance, and transparent routing logs.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.registry import registry
from app.models.base import ModelOutput
from app.models.scenario_matcher import match_demo_scenario
from app.core.evidence import build_demo_evidence, build_real_evidence, no_spatial_evidence_available
from app.core.fusion import compute_confidence, HeuristicConfidence
from app.core.validator import FileMetadata
from app.core import trace as tracer


def route_and_execute(
    db: Session,
    job_id: str,
    image_paths: list[str],
    query: str,
    primary_task: str,
    subtasks: list[dict],
    query_confidence: float,
    compatibility_score: float,
    compatibility_warning: bool,
    warning_reason: Optional[str],
    temporal_pair: bool,
    file_metas: Optional[list[FileMetadata]] = None,
) -> dict:
    """
    Execute the agentic pipeline steps 4–8.
    Returns the assembled result dict (to be stored in Job.result).
    """
    mode = settings.MODE
    file_metas = file_metas or []
    input_filenames = [m.original_filename for m in file_metas]

    # Step 4: Select specialist model / scenario
    tracer.start_step(db, job_id, 3)
    scenario_data = None

    try:
        specialist = registry.get_model_for_task(primary_task)
        model_info = specialist.model_info

        if mode == "demo":
            scenario_data, trace_info = match_demo_scenario(
                query=query,
                task_type=primary_task,
                file_metas=file_metas
            )
            if scenario_data:
                sc_id = scenario_data.get("scenario_id", "demo")
                routing_decision = {
                    "scenario_match": sc_id,
                    "matched_task": trace_info.get("matched_task", primary_task),
                    "matched_intent": trace_info.get("matched_intent", "primary land-cover classification"),
                    "matched_fixture": trace_info.get("matched_fixture", "fixture_a_optical"),
                    "input_fixture_file": input_filenames,
                    "task_interpretation": primary_task,
                    "scenario_selected_or_model_selected": f"scenario: {sc_id}",
                    "why_selected": trace_info["why_selected"],
                    "capabilities_used": [primary_task],
                    "evidence_source": "demo-scenario",
                }
                tracer_msg = (
                    f"Scenario Match: {sc_id} | Task: {trace_info.get('matched_task')} | "
                    f"Intent: {trace_info.get('matched_intent')} | Fixture: {trace_info.get('matched_fixture')}"
                )
            else:
                routing_decision = {
                    "scenario_match": "none",
                    "matched_task": "none",
                    "matched_intent": "none",
                    "matched_fixture": "none",
                    "input_fixture_file": input_filenames,
                    "task_interpretation": primary_task,
                    "scenario_selected_or_model_selected": "none (unmatched)",
                    "why_selected": trace_info.get("why_selected", "No matching Demo Scenario is available for this query/input combination."),
                    "capabilities_used": [],
                    "evidence_source": "none",
                }
                tracer_msg = f"No matching Demo Scenario for query/fixture combination. No fallback used."
        else:
            # Real Mode
            supported_tasks = model_info.capabilities.tasks
            is_supported = primary_task in supported_tasks
            if is_supported:
                routing_decision = {
                    "scenario_match": "none",
                    "matched_task": primary_task,
                    "matched_intent": "real-model-inference",
                    "matched_fixture": "uploaded-imagery",
                    "input_fixture_file": input_filenames,
                    "task_interpretation": primary_task,
                    "scenario_selected_or_model_selected": f"model: {model_info.name}",
                    "why_selected": f"Task '{primary_task}' is supported by loaded model {model_info.name} ({model_info.encoder}).",
                    "capabilities_used": [primary_task],
                    "evidence_source": "real-specialist-model",
                }
                tracer_msg = f"Selected Model: {model_info.name} ({model_info.encoder}) | Source: real-specialist-model"
            else:
                routing_decision = {
                    "scenario_match": "none",
                    "matched_task": "none",
                    "matched_intent": "none",
                    "matched_fixture": "uploaded-imagery",
                    "input_fixture_file": input_filenames,
                    "task_interpretation": primary_task,
                    "scenario_selected_or_model_selected": f"model: {model_info.name} (unsupported task)",
                    "why_selected": f"Task '{primary_task}' is unsupported by the loaded {model_info.encoder} checkpoint. No task head available.",
                    "capabilities_used": [],
                    "evidence_source": "none",
                }
                tracer_msg = f"Selected Model: {model_info.name} | Task '{primary_task}' unsupported by {model_info.encoder} checkpoint."

        tracer.complete_step(db, job_id, 3, message=tracer_msg, detail=routing_decision)

    except ValueError as e:
        tracer.error_step(db, job_id, 3, str(e))
        tracer.skip_remaining_steps(db, job_id, 4)
        return {"error": str(e), "status": "error"}

    # Step 5: Run model inference
    tracer.start_step(db, job_id, 4)
    try:
        if mode == "demo":
            if scenario_data:
                output = specialist.run_inference(
                    image_paths=image_paths,
                    query=query,
                    task_type=primary_task,
                    subtasks=subtasks,
                    mode=mode,
                    scenario_data=scenario_data,
                )
            else:
                # Never fall back to a random canned answer
                output = ModelOutput(
                    answer=None,
                    model_confidence=None,
                    evidence=[],
                    grounding_supported=False,
                    counting_result=None,
                    subtask_outputs=[],
                    raw_output={
                        "error": "No matching Demo Scenario is available for this query/input combination.",
                        "supported": False
                    },
                )
        else:
            output = specialist.run_inference(
                image_paths=image_paths,
                query=query,
                task_type=primary_task,
                subtasks=subtasks,
                mode=mode,
            )

        inf_msg = (
            f"Inference complete. Answer: {str(output.answer)[:80]}"
            if output.answer
            else f"Task unsupported: {output.raw_output.get('error', 'No answer')}"
        )
        tracer.complete_step(db, job_id, 4, message=inf_msg, detail={"supported": output.answer is not None, "why": routing_decision["why_selected"]})

    except Exception as e:
        tracer.error_step(db, job_id, 4, f"Model inference failed: {str(e)}")
        tracer.skip_remaining_steps(db, job_id, 5)
        return {"error": f"Model inference failed: {str(e)}", "status": "error"}

    # Step 6: Fusion (only for multi-sensor or temporal tasks)
    tracer.start_step(db, job_id, 5)
    tracer.complete_step(db, job_id, 5,
        message="Fusion step" + (" applied for temporal pair" if temporal_pair else " not required for single-image task")
    )

    # Step 7: Confidence estimation
    tracer.start_step(db, job_id, 6)
    if output.answer is None:
        # Do not produce high confidence if no scenario matched or task is unsupported
        heuristic_conf = HeuristicConfidence(
            query_confidence=round(query_confidence, 4),
            compatibility_score=round(compatibility_score, 4),
            model_confidence=None,
            evidence_consistency=None,
            final_confidence=0.0,
            capped=True,
            cap_reason="Task unsupported by available scenario/model; no answer produced.",
        )
    else:
        heuristic_conf = compute_confidence(
            query_confidence=query_confidence,
            compatibility_score=compatibility_score,
            model_confidence=output.model_confidence,
            evidence_consistency=output.raw_output.get("evidence_consistency") if output.raw_output else None,
            compatibility_warning=compatibility_warning,
            warning_reason=warning_reason,
        )

    tracer.complete_step(db, job_id, 6,
        message=f"Final heuristic confidence: {heuristic_conf.final_confidence:.3f}",
        detail=heuristic_conf.to_dict()
    )

    # Step 8: Evidence generation
    tracer.start_step(db, job_id, 7)
    if output.answer is None or not output.evidence:
        evidence_items = no_spatial_evidence_available()
    else:
        if mode == "demo":
            evidence_items = build_demo_evidence(output.evidence)
        else:
            if output.grounding_supported and output.evidence:
                evidence_items = build_real_evidence(output.evidence)
            else:
                evidence_items = no_spatial_evidence_available()

    tracer.complete_step(db, job_id, 7,
        message=f"{len(evidence_items)} evidence item(s) generated",
        detail={"grounding_supported": output.grounding_supported and output.answer is not None, "evidence_count": len(evidence_items)}
    )

    # Step 9: Assemble trace
    tracer.start_step(db, job_id, 8)
    tracer.complete_step(db, job_id, 8, message="Execution trace assembled.")

    # Build subtask results
    subtask_results = []
    for i, sub in enumerate(subtasks):
        is_supported = (output.answer is not None)
        subtask_results.append({
            "subtask_id": sub.get("subtask_id", f"sub_{i+1}"),
            "task_type": sub.get("task_type", primary_task),
            "query_fragment": sub.get("query_fragment", query),
            "supported": is_supported,
            "limitation_message": (
                None if is_supported
                else (output.raw_output.get("error") if output.raw_output else "No matching Demo Scenario is available for this query/input combination.")
            ),
            "answer": output.answer,
            "count": output.counting_result.get("count") if output.counting_result else None,
            "count_note": output.counting_result.get("note") if output.counting_result else None,
            "evidence": [e.to_dict() for e in evidence_items],
            "grounding_supported": output.grounding_supported and is_supported,
        })

    tokens = [m.token for m in file_metas]
    preview_url = f"/api/files/{tokens[0]}/preview" if tokens else None
    return {
        "status": "completed",
        "task_type": primary_task,
        "model_info": model_info.to_dict(),
        "routing_decision": routing_decision,
        "subtasks": subtask_results,
        "heuristic_confidence": heuristic_conf.to_dict(),
        "temporal_pair": temporal_pair,
        "grounding_supported": output.grounding_supported and (output.answer is not None),
        "file_tokens": tokens,
        "file_url": preview_url,
        "preview_url": preview_url,
        "preview_urls": [f"/api/files/{t}/preview" for t in tokens],
    }
