"""
Regression Test Suite for SatQuery AI Input/Query-Aware Routing,
Intent Flexibility, Grounding Integrity, and Image Display.
"""
import pytest
import uuid
import io
from pathlib import Path
from PIL import Image
from app.config import settings
from app.core.validator import FileMetadata
from app.core.compatibility import check_compatibility
from app.core.interpreter import interpret_query
from app.core.controller import route_and_execute
from app.models.scenario_matcher import match_demo_scenario
from app.models.registry import ModelRegistry, registry
from app.db.database import SessionLocal, init_db
from app.db.models import UploadedFile
from app.core import trace as tracer


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()


def make_file_meta(name: str, modality: str = "optical", gsd: float = 10.0, label: str = "single", path: str = "") -> FileMetadata:
    return FileMetadata(
        token=str(uuid.uuid4()),
        original_filename=name,
        saved_path=path or f"fixtures/{name}",
        file_size_bytes=2048,
        modality=modality,
        gsd_meters=gsd,
        band_count=3,
        width_px=512,
        height_px=512,
        crs=None,
        valid=True,
        validation_error=None,
    )


# ── Test 1: Agricultural land-cover query + correct demo fixture => matching scenario
def test_1_agricultural_query_matches_scenario():
    db = SessionLocal()
    f_optical = make_file_meta("sample_optical_2023.tif")
    q = "Is agricultural land the primary land cover in this scene?"
    interp = interpret_query(q)

    sc, trace_info = match_demo_scenario(q, interp.primary_task, [f_optical])
    assert sc is not None
    assert sc["scenario_id"] == "rs-vqa-binary-landcover"
    assert trace_info["matched_task"] in ("binary-vqa", "rs-vqa-binary")
    assert trace_info["matched_intent"] == "primary land-cover classification"
    assert trace_info["matched_fixture"] == "fixture_a_optical"

    j = str(uuid.uuid4())
    tracer.init_trace(db, j)
    r = route_and_execute(
        db=db, job_id=j, image_paths=[f_optical.saved_path], query=q,
        primary_task=interp.primary_task,
        subtasks=[{"subtask_id": "s1", "task_type": interp.primary_task, "query_fragment": q}],
        query_confidence=interp.confidence, compatibility_score=1.0,
        compatibility_warning=False, warning_reason=None,
        temporal_pair=False, file_metas=[f_optical]
    )
    db.close()

    assert r["subtasks"][0]["supported"] is True
    assert "agricultural land" in r["subtasks"][0]["answer"].lower()
    assert r["routing_decision"]["scenario_match"] == "rs-vqa-binary-landcover"
    assert r["routing_decision"]["matched_fixture"] == "fixture_a_optical"


# ── Test 2: Reworded agricultural queries + same fixture => same scenario ────
@pytest.mark.parametrize("reworded_query", [
    "Is this scene mainly agricultural?",
    "Does agriculture dominate this scene?",
    "Is agriculture the main land cover here?",
    "Is cropland present in this scene?",
])
def test_2_reworded_agricultural_query_matches_same_scenario(reworded_query):
    f_optical = make_file_meta("sample_optical_2023.tif")
    interp = interpret_query(reworded_query)
    sc, trace_info = match_demo_scenario(reworded_query, interp.primary_task, [f_optical])

    assert sc is not None, f"Reworded query '{reworded_query}' should match agricultural scenario"
    assert sc["scenario_id"] == "rs-vqa-binary-landcover"
    assert trace_info["matched_intent"] == "primary land-cover classification"
    assert trace_info["matched_fixture"] == "fixture_a_optical"


# ── Test 3: Unrelated query + same fixture => no matching scenario ───────────
def test_3_unrelated_query_same_fixture_no_match():
    db = SessionLocal()
    f_optical = make_file_meta("sample_optical_2023.tif")
    q_unrelated = "Are there military airplanes parked on the runway?"
    interp = interpret_query(q_unrelated)

    sc, trace_info = match_demo_scenario(q_unrelated, interp.primary_task, [f_optical])
    assert sc is None
    assert trace_info["scenario_match"] == "none"

    j = str(uuid.uuid4())
    tracer.init_trace(db, j)
    r = route_and_execute(
        db=db, job_id=j, image_paths=[f_optical.saved_path], query=q_unrelated,
        primary_task=interp.primary_task,
        subtasks=[{"subtask_id": "s1", "task_type": interp.primary_task, "query_fragment": q_unrelated}],
        query_confidence=interp.confidence, compatibility_score=1.0,
        compatibility_warning=False, warning_reason=None,
        temporal_pair=False, file_metas=[f_optical]
    )
    db.close()

    sub = r["subtasks"][0]
    assert sub["supported"] is False
    assert sub["answer"] is None
    assert "No matching Demo Scenario is available" in sub["limitation_message"]
    assert len(sub["evidence"]) == 0
    assert r["heuristic_confidence"]["final_confidence"] == 0.0


# ── Test 4: Agricultural query + unrelated fixture => no matching scenario ───
def test_4_agricultural_query_unrelated_fixture_no_match():
    f_unrelated = make_file_meta("arbitrary_city_photo.jpg", path="arbitrary_city_photo.jpg")
    q = "Is agricultural land the primary land cover in this scene?"
    interp = interpret_query(q)

    sc, trace_info = match_demo_scenario(q, interp.primary_task, [f_unrelated])
    assert sc is None
    assert trace_info["scenario_match"] == "none"


# ── Test 5: Unsupported query => actual image still displayed in result ───────
def test_5_unsupported_query_actual_image_still_displayed():
    db = SessionLocal()
    f_optical = make_file_meta("sample_optical_2023.tif")

    # Register file in database so preview endpoint can serve it
    db_file = UploadedFile(
        token=f_optical.token,
        original_filename=f_optical.original_filename,
        saved_path="fixtures/sample_optical_2023.tif",
        file_size_bytes=2048,
        modality="optical",
        gsd_meters=10.0,
        band_count=3,
        width_px=512,
        height_px=512,
    )
    db.add(db_file)
    db.commit()

    q_unsupported = "Detect maritime vessels in the harbor"
    interp = interpret_query(q_unsupported)
    j = str(uuid.uuid4())
    tracer.init_trace(db, j)
    r = route_and_execute(
        db=db, job_id=j, image_paths=[f_optical.saved_path], query=q_unsupported,
        primary_task=interp.primary_task,
        subtasks=[{"subtask_id": "s1", "task_type": interp.primary_task, "query_fragment": q_unsupported}],
        query_confidence=interp.confidence, compatibility_score=1.0,
        compatibility_warning=False, warning_reason=None,
        temporal_pair=False, file_metas=[f_optical]
    )
    db.close()

    # The result must include the actual image preview URL and tokens
    assert r["file_url"] is not None
    assert r["file_tokens"] == [f_optical.token]
    assert r["preview_url"] == f"/api/files/{f_optical.token}/preview"

    # Verify preview generation directly
    with Image.open("fixtures/sample_optical_2023.tif") as img:
        assert img.size == (512, 512)


# ── Test 6: One image + temporal query => incompatible ────────────────────────
def test_6_one_image_temporal_query_incompatible():
    f_optical = make_file_meta("sample_optical_2023.tif")
    compat = check_compatibility([f_optical], task_type="change-vqa", temporal_pair=True)

    assert compat.status == "incompatible"
    assert compat.compatibility_score == 0.0
    assert "two temporal observations" in compat.message.lower()


# ── Test 7: Valid two-observation pair => Change-VQA executes ─────────────────
def test_7_valid_two_image_temporal_pair_change_vqa():
    db = SessionLocal()
    f_2023 = make_file_meta("sample_optical_2023.tif", label="t1")
    f_2024 = make_file_meta("sample_optical_2024.tif", label="t2")

    compat = check_compatibility([f_2023, f_2024], task_type="change-vqa", temporal_pair=True)
    assert compat.status == "compatible"

    q = "Has urban built-up area expanded between the two dates?"
    j = str(uuid.uuid4())
    tracer.init_trace(db, j)
    r = route_and_execute(
        db=db, job_id=j, image_paths=[f_2023.saved_path, f_2024.saved_path], query=q,
        primary_task="change-vqa",
        subtasks=[{"subtask_id": "s1", "task_type": "change-vqa", "query_fragment": q}],
        query_confidence=0.9, compatibility_score=1.0,
        compatibility_warning=False, warning_reason=None,
        temporal_pair=True, file_metas=[f_2023, f_2024]
    )
    db.close()

    assert r["routing_decision"]["scenario_match"] == "change-vqa-urban-expansion"
    assert r["routing_decision"]["matched_fixture"] == "fixture_b_temporal_pair"
    assert r["subtasks"][0]["supported"] is True
    assert len(r["subtasks"][0]["evidence"]) == 1
    assert r["subtasks"][0]["evidence"][0]["coordinates"] == [120, 80, 310, 270]


# ── Test 8: Real Mode honesty & Generic CLIP labeling ─────────────────────────
def test_8_real_mode_honesty_and_generic_clip_labeling():
    orig_mode = settings.MODE
    orig_path = settings.RS_VQA_MODEL_PATH
    settings.MODE = "real"
    settings.RS_VQA_MODEL_PATH = ""

    try:
        reg = ModelRegistry()
        for m in reg.list_all():
            assert m["encoder"] == "generic-fallback"
            assert m["capabilities"]["grounding_supported"] is False
            assert "generic" in m["inference_provenance"].lower()
    finally:
        settings.MODE = orig_mode
        settings.RS_VQA_MODEL_PATH = orig_path
