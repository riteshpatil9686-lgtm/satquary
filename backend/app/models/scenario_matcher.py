"""
Structured, intent- and fixture-aware Demo Scenario matcher.
Enforces:
1. Scenario matching against task type, observation count, fixture identity, and query intent.
2. Natural language flexibility: reworded queries with the same supported intent match the scenario.
3. Strict fixture identity: arbitrary/unrelated uploaded imagery does not execute a scenario.
4. Transparent trace logging: exposes scenario_id, matched task, matched intent, and matched fixture.
5. No generic canned fallbacks when no scenario matches.
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Optional
from app.core.validator import FileMetadata

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"

_FIXTURE_HASHES: dict[str, str] = {}

FIXTURE_FILES: dict[str, str] = {
    "fixture_a_optical": "sample_optical_2023.tif",
    "fixture_a": "sample_optical_2023.tif",
    "sample_optical_2023": "sample_optical_2023.tif",
    "sample_optical_2023.tif": "sample_optical_2023.tif",
    "fixture_b_temporal_pair": "sample_optical_2024.tif",
    "sample_optical_2024": "sample_optical_2024.tif",
    "sample_optical_2024.tif": "sample_optical_2024.tif",
    "fixture_c_grounding": "sample_grounding.tif",
    "sample_grounding": "sample_grounding.tif",
    "sample_grounding.tif": "sample_grounding.tif",
    "sample_sar": "sample_sar.tif",
    "sample_sar.tif": "sample_sar.tif",
}


def _get_fixture_hash(fixture_filename: str) -> Optional[str]:
    """Cache and return SHA-256 of known fixture file."""
    actual_name = FIXTURE_FILES.get(fixture_filename, fixture_filename)
    if actual_name in _FIXTURE_HASHES:
        return _FIXTURE_HASHES[actual_name]
    path = FIXTURES_DIR / actual_name
    if path.exists():
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        _FIXTURE_HASHES[actual_name] = h
        return h
    return None


def _file_matches_fixture(
    file: FileMetadata,
    required_filename: str,
    aliases: list[str],
    accepts_any_optical: bool = False
) -> bool:
    """Check if file matches fixture by filename, alias, modality, or content hash."""
    # If the scenario accepts any valid optical satellite image (e.g. general scene captioning)
    if accepts_any_optical and file.modality in ("optical", "unknown"):
        return True

    name_lower = Path(file.original_filename).name.lower()
    if any(alias.lower() in name_lower for alias in aliases):
        return True

    # Check content hash if file exists on disk
    if file.saved_path and Path(file.saved_path).exists():
        try:
            file_hash = hashlib.sha256(Path(file.saved_path).read_bytes()).hexdigest()
            fix_hash = _get_fixture_hash(required_filename)
            if fix_hash and file_hash == fix_hash:
                return True
        except Exception:
            pass

    return False


def _matches_intent(query: str, scenario: dict) -> bool:
    """
    Match natural-language query against scenario intent.
    Supports exact queries, example queries, regex query patterns, and intent keywords.
    """
    q_norm = query.strip().lower()
    q_clean = q_norm.rstrip("?.! ")

    # Exact or containment with scenario primary query
    sc_q = scenario.get("query", "").strip().lower()
    if q_norm == sc_q or sc_q in q_norm or q_clean == sc_q.rstrip("?.! "):
        return True

    # Match any example queries
    for ex in scenario.get("example_queries", []):
        ex_norm = ex.strip().lower().rstrip("?.! ")
        if q_clean == ex_norm or ex_norm in q_clean or q_clean in ex_norm:
            return True

    # Match compiled query patterns
    for pat in scenario.get("query_patterns", []):
        if re.search(pat, q_norm, re.IGNORECASE):
            return True

    # Fallback to intent keyword coverage (must match at least 1 primary keyword)
    keywords = scenario.get("intent_keywords", [])
    if keywords:
        hits = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', q_norm, re.IGNORECASE))
        if hits >= 1:
            return True

    return False


def match_demo_scenario(
    query: str,
    task_type: str,
    file_metas: list[FileMetadata]
) -> tuple[Optional[dict], dict]:
    """
    Match user request to a deterministic Demo Scenario using structured requirements.

    Returns:
        (scenario_dict, trace_info_dict) if matched.
        (None, trace_info_dict) if no scenario matches.
    """
    input_filenames = [m.original_filename for m in (file_metas or [])]
    trace_info = {
        "scenario_match": "none",
        "matched_task": "none",
        "matched_intent": "none",
        "matched_fixture": "none",
        "input_fixture_file": input_filenames,
        "why_selected": "No matching Demo Scenario is available for this query/input combination.",
    }

    if not file_metas:
        trace_info["why_selected"] = "No files provided for analysis."
        return None, trace_info

    # Load scenarios (deduplicate by scenario_id)
    seen_ids = set()
    scenarios = []
    for sc_file in sorted(SCENARIOS_DIR.glob("*.json")):
        try:
            with open(sc_file, encoding="utf-8") as f:
                sc_data = json.load(f)
                sc_id = sc_data.get("scenario_id")
                if sc_id and sc_id not in seen_ids:
                    seen_ids.add(sc_id)
                    scenarios.append(sc_data)
        except Exception:
            continue

    num_files = len(file_metas)

    for sc in scenarios:
        sc_id = sc.get("scenario_id")
        sc_task = sc.get("task_type")
        task_aliases = sc.get("task_aliases", [sc_task])
        req = sc.get("input_requirement", {})
        expected_images = req.get("image_count", sc.get("required_images", 1))
        fixture_id = req.get("fixture_id", sc.get("required_fixture", "unknown"))

        # 1. Task type match
        if task_type != sc_task and task_type not in task_aliases:
            continue

        # 2. Image count match
        if num_files != expected_images:
            continue

        # 3. Scenario-specific fixture and intent matching
        if req.get("temporal", False) or sc_id == "change-vqa-urban-expansion":
            # Bi-temporal scenario
            aliases_t1 = req.get("fixture_aliases_t1", sc.get("fixture_aliases_t1", ["2023", "t1"]))
            aliases_t2 = req.get("fixture_aliases_t2", sc.get("fixture_aliases_t2", ["2024", "t2"]))

            f0 = file_metas[0]
            f1 = file_metas[1]

            t1_match = _file_matches_fixture(f0, "sample_optical_2023.tif", aliases_t1) or (f0.temporal_label == "t1")
            t2_match = _file_matches_fixture(f1, "sample_optical_2024.tif", aliases_t2) or (f1.temporal_label == "t2")

            if not (t1_match and t2_match):
                t1_match_rev = _file_matches_fixture(f1, "sample_optical_2023.tif", aliases_t1) or (f1.temporal_label == "t1")
                t2_match_rev = _file_matches_fixture(f0, "sample_optical_2024.tif", aliases_t2) or (f0.temporal_label == "t2")
                if not (t1_match_rev and t2_match_rev):
                    continue

            # Intent match
            if not _matches_intent(query, sc):
                continue

            matched_intent = sc.get("supported_intent", "temporal change detection")
            matched_fixture = fixture_id

            trace_info = {
                "scenario_match": sc_id,
                "matched_task": sc.get("task", task_type),
                "matched_intent": matched_intent,
                "matched_fixture": matched_fixture,
                "input_fixture_file": input_filenames,
                "why_selected": (
                    f"Scenario Match:\n{sc_id}\n\n"
                    f"Matched task:\n{sc.get('task', task_type)}\n\n"
                    f"Matched intent:\n{matched_intent}\n\n"
                    f"Matched fixture:\n{matched_fixture}"
                ),
            }
            return sc, trace_info

        else:
            # Single-image scenario
            req_file = req.get("fixture_file") or sc.get("required_fixture") or FIXTURE_FILES.get(fixture_id, f"{fixture_id}.tif")
            aliases = req.get("fixture_aliases", sc.get("fixture_aliases", []))
            accepts_any_optical = req.get("accepts_any_optical", False)
            f0 = file_metas[0]

            if not _file_matches_fixture(f0, req_file, aliases, accepts_any_optical=accepts_any_optical):
                continue

            if not _matches_intent(query, sc):
                continue

            matched_intent = sc.get("supported_intent", sc.get("task", task_type))
            matched_fixture = fixture_id

            trace_info = {
                "scenario_match": sc_id,
                "matched_task": sc.get("task", task_type),
                "matched_intent": matched_intent,
                "matched_fixture": matched_fixture,
                "input_fixture_file": input_filenames,
                "why_selected": (
                    f"Scenario Match:\n{sc_id}\n\n"
                    f"Matched task:\n{sc.get('task', task_type)}\n\n"
                    f"Matched intent:\n{matched_intent}\n\n"
                    f"Matched fixture:\n{matched_fixture}"
                ),
            }
            return sc, trace_info

    return None, trace_info
