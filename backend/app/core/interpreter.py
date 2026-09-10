"""
Natural-language query interpreter.
Uses keyword/pattern classification — no external LLM dependency in Tier 1.
Returns task type, subtask decomposition, and calibrated confidence.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


# Task type identifiers (mirror BigEarthNet.txt task categories)
TASK_TYPES = {
    "rs-vqa-binary": "Binary yes/no question about scene content",
    "rs-vqa-mcq": "Multiple-choice question about scene properties",
    "captioning": "Describe or caption the satellite scene",
    "grounding": "Locate or detect a region/object (referring expression detection)",
    "change-vqa": "Analyse change between two temporal observations",
    "fusion": "Combine optical and SAR information for analysis",
}


@dataclass
class SubtaskSpec:
    subtask_id: str
    task_type: str
    query_fragment: str
    confidence: float


@dataclass
class InterpretationResult:
    primary_task: str
    subtasks: list[SubtaskSpec]
    confidence: float          # 0–1 — calibrated heuristic, not invented
    needs_clarification: bool
    clarification_candidates: list[dict]   # [{task, description}]
    temporal_intent: bool      # True if query implies before/after comparison
    multi_part: bool


# ── Keyword pattern tables ────────────────────────────────────────────────────

_CHANGE_PATTERNS = [
    r'\b(change|changed|changing|expansion|expanded|shrink|shrunk|grew|grow)\b',
    r'\b(before|after|between|compared to|versus|vs\.?|temporal|over time)\b',
    r'\b(2[0-9]{3})\s*(to|-|and|vs)\s*(2[0-9]{3})\b',  # year-to-year
    r'\b(deforestation|urbanis|urbaniz|flood\w*|construction)\b',
]

_GROUNDING_PATTERNS = [
    r'\b(locate|find|identify|detect|where|show me|highlight|mark|bbox|bounding box)\b',
    r'\b(region|area|zone|sector|patch|segment|spot)\b',
    r'\b(solar panel|building|road|river|lake|forest patch|field|warehouse)\b',
]

_CAPTIONING_PATTERNS = [
    r'\b(describe|caption|summarize|what does|tell me about|overview|what is in)\b',
    r'\b(describe the scene|explain|characterize)\b',
]

_BINARY_PATTERNS = [
    r'\b(is|are|has|have|does|do)\b.{0,40}\b(present|there|visible|detected|exist)\b',
    r'\b(yes or no|true or false)\b',
    r'^(is |are |has |have |does |do )',
]

_MCQ_PATTERNS = [
    r'\bwhat\b.{0,30}\b(type|kind|class|category|percentage|proportion|fraction|amount|land cover)\b',
    r'\bwhich\b.{0,30}\b(class|type|land use|land cover|category)\b',
    r'\b(how much|how many|what proportion)\b',
    r'\b(primary|dominant|main|majority)\b.{0,30}\b(land|cover|class|type)\b',
]

_FUSION_PATTERNS = [
    r'\b(sar|synthetic aperture|radar)\b',
    r'\b(optical and sar|sar and optical|multi.?sensor|fuse|fusion)\b',
]

# Subtask split markers (for multi-part queries)
_SUBTASK_SPLITTERS = [
    r'\band\b',
    r'\balso\b',
    r'\badditionally\b',
    r'\bfurthermore\b',
    r'\bmoreover\b',
]


def _match_score(text: str, patterns: list[str]) -> float:
    """Return fraction of patterns matched (0–1)."""
    if not patterns:
        return 0.0
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return hits / len(patterns)


def _classify_fragment(fragment: str) -> tuple[str, float]:
    """Classify a single query fragment. Returns (task_type, confidence)."""
    text = fragment.strip().lower()

    scores = {
        "change-vqa":    min(1.0, _match_score(text, _CHANGE_PATTERNS) * 2.5),
        "grounding":     min(1.0, _match_score(text, _GROUNDING_PATTERNS) * 2.0),
        "captioning":    min(1.0, _match_score(text, _CAPTIONING_PATTERNS) * 3.0),
        "rs-vqa-binary": min(1.0, _match_score(text, _BINARY_PATTERNS) * 2.5),
        "rs-vqa-mcq":    min(1.0, _match_score(text, _MCQ_PATTERNS) * 2.0),
        "fusion":        min(1.0, _match_score(text, _FUSION_PATTERNS) * 4.0),
    }

    best_task = max(scores, key=scores.get)
    best_score = scores[best_task]

    # Fallback heuristic: question starts with "is/are/has" → binary
    if best_score < 0.15:
        if re.match(r'^(is |are |has |have |does |do )', text):
            return "rs-vqa-binary", 0.50
        return "rs-vqa-binary", 0.30  # most common default

    return best_task, round(best_score, 3)


def _split_into_fragments(query: str) -> list[str]:
    """
    Try to split multi-part query into constituent fragments.
    E.g. "Count solar panels and identify warehouses" → 2 fragments.
    Only splits when both fragments are meaningful (>= 4 words each).
    """
    # Try splitting by comma + "and"
    parts = re.split(r',\s*and\s+|;\s*', query)
    if len(parts) == 1:
        # Try splitting on "and" followed by a verb/imperative
        parts = re.split(r'\band\b(?=\s+\w+)', query, maxsplit=1)

    fragments = [p.strip() for p in parts if len(p.strip().split()) >= 3]
    return fragments if len(fragments) > 1 else [query.strip()]


def interpret_query(query: str, threshold: float = 0.6) -> InterpretationResult:
    """
    Interpret a natural-language remote sensing query.
    Returns an InterpretationResult — never invents detections or evidence.
    """
    query = query.strip()
    if not query:
        return InterpretationResult(
            primary_task="rs-vqa-binary", subtasks=[],
            confidence=0.0, needs_clarification=True,
            clarification_candidates=[
                {"task": "rs-vqa-binary", "description": "Answer a yes/no question about the scene"},
                {"task": "captioning", "description": "Describe the satellite scene content"},
            ],
            temporal_intent=False, multi_part=False
        )

    # Check temporal intent (before running per-task classification)
    temporal_intent = bool(re.search(
        r'\b(change|before|after|between|2[0-9]{3}\s*(to|-)\s*2[0-9]{3}|temporal|over time|compare)\b',
        query, re.IGNORECASE
    ))

    # If temporal intent but task seems grounding → upgrade to change-vqa
    fragments = _split_into_fragments(query)
    multi_part = len(fragments) > 1

    subtasks = []
    for i, frag in enumerate(fragments):
        task_type, conf = _classify_fragment(frag)
        # Temporal intent overrides single-image tasks for change-related verbs
        if temporal_intent and task_type in ("rs-vqa-binary", "rs-vqa-mcq", "captioning"):
            if re.search(r'\b(change|expand|shrink|grow|deforest|flood|built)\w*\b', frag, re.IGNORECASE):
                task_type = "change-vqa"
                conf = max(conf, 0.70)
        subtasks.append(SubtaskSpec(
            subtask_id=f"sub_{i+1}",
            task_type=task_type,
            query_fragment=frag,
            confidence=conf,
        ))

    primary_task = subtasks[0].task_type if subtasks else "rs-vqa-binary"
    overall_confidence = round(sum(s.confidence for s in subtasks) / len(subtasks), 3)

    needs_clarification = overall_confidence < threshold

    clarification_candidates = []
    if needs_clarification:
        # Build top-2 alternatives
        _, conf2 = _classify_fragment(query)
        all_scores = {}
        for tt in TASK_TYPES:
            _, sc = _classify_fragment(query)
            all_scores[tt] = sc
        # Include primary and second-best
        sorted_tasks = sorted(all_scores.items(), key=lambda x: -x[1])
        clarification_candidates = [
            {"task": t, "description": TASK_TYPES[t]}
            for t, _ in sorted_tasks[:2]
        ]

    return InterpretationResult(
        primary_task=primary_task,
        subtasks=subtasks,
        confidence=overall_confidence,
        needs_clarification=needs_clarification,
        clarification_candidates=clarification_candidates,
        temporal_intent=temporal_intent,
        multi_part=multi_part,
    )
