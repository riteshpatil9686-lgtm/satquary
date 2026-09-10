"""
BigEarthNet.txt Metrics
════════════════════════

Evaluation metrics for all 4 task categories:
  - Binary VQA: Accuracy (exact match yes/no)
  - MCQ VQA: Accuracy (top-1 choice match)
  - Captioning: BLEU-4, METEOR, CIDEr (requires nltk/pycocoevalcap)
  - Grounding (Referring Expr Det): IoU, mAP@0.50, mAP@0.75
"""
from typing import Optional


def binary_vqa_accuracy(predictions: list[str], targets: list[str]) -> dict:
    """Exact match accuracy for binary yes/no VQA."""
    assert len(predictions) == len(targets), "Length mismatch"
    correct = sum(p.strip().lower() == t.strip().lower() for p, t in zip(predictions, targets))
    return {
        "accuracy": round(correct / len(targets), 4) if targets else 0.0,
        "n_samples": len(targets),
        "n_correct": correct,
    }


def mcq_accuracy(predictions: list[str], targets: list[str]) -> dict:
    """Top-1 accuracy for MCQ VQA."""
    return binary_vqa_accuracy(predictions, targets)


def grounding_iou(pred_bbox: list[int], gt_bbox: list[int]) -> float:
    """Compute IoU between predicted and ground-truth bounding boxes."""
    px1, py1, px2, py2 = pred_bbox
    gx1, gy1, gx2, gy2 = gt_bbox

    inter_x1 = max(px1, gx1)
    inter_y1 = max(py1, gy1)
    inter_x2 = min(px2, gx2)
    inter_y2 = min(py2, gy2)

    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    pred_area = (px2 - px1) * (py2 - py1)
    gt_area = (gx2 - gx1) * (gy2 - gy1)
    union_area = pred_area + gt_area - inter_area

    return round(inter_area / union_area, 4) if union_area > 0 else 0.0


def grounding_accuracy_at_iou(
    predictions: list[list[int]],
    targets: list[list[int]],
    iou_threshold: float = 0.50,
) -> dict:
    """Compute Acc@IoU for grounding. A prediction is correct if IoU ≥ threshold."""
    assert len(predictions) == len(targets), "Length mismatch"
    ious = [grounding_iou(p, t) for p, t in zip(predictions, targets)]
    n_correct = sum(iou >= iou_threshold for iou in ious)
    return {
        f"acc@iou{int(iou_threshold * 100)}": round(n_correct / len(ious), 4) if ious else 0.0,
        "mean_iou": round(sum(ious) / len(ious), 4) if ious else 0.0,
        "n_samples": len(ious),
    }


def captioning_bleu4(predictions: list[str], references: list[list[str]]) -> dict:
    """BLEU-4 score via sacrebleu. Returns 0.0 if sacrebleu not installed."""
    try:
        from sacrebleu.metrics import BLEU
        bleu = BLEU(max_ngram_order=4, smooth_method='add-k')
        result = bleu.corpus_score(predictions, references)
        return {"bleu4": round(result.score / 100, 4)}
    except ImportError:
        return {"bleu4": None, "note": "sacrebleu not installed"}
