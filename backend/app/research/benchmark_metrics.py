import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from backend.app.research.adapters.base import BenchmarkSample

class BenchmarkInvalidityError(ValueError):
    """
    Raised when benchmark validation detects circular ground-truth derivation,
    synthetic data contamination in a real track, or invalid evaluation protocols.
    """
    pass

def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    valid_mask: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Computes rigorous raster evaluation metrics: IoU, Dice (F1), Precision, Recall, FDR.
    Optionally masks out invalid/cloud/no-data pixels.
    """
    if valid_mask is not None:
        yt = y_true[valid_mask].astype(bool)
        yp = y_pred[valid_mask].astype(bool)
    else:
        yt = y_true.astype(bool)
        yp = y_pred.astype(bool)

    tp = int(np.sum(yt & yp))
    fp = int(np.sum((~yt) & yp))
    fn = int(np.sum(yt & (~yp)))
    tn = int(np.sum((~yt) & (~yp)))

    total_valid = tp + fp + fn + tn
    iou = float(tp / max(1, tp + fp + fn))
    precision = float(tp / max(1, tp + fp))
    recall = float(tp / max(1, tp + fn))
    f1 = float(2 * precision * recall / max(1e-7, precision + recall))
    fdr = float(fp / max(1, tp + fp))

    return {
        "iou": round(iou, 4),
        "f1": round(f1, 4),
        "dice": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_discovery_rate": round(fdr, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "valid_pixels": int(total_valid)
    }

def validate_benchmark_integrity(
    sample: BenchmarkSample,
    y_pred: np.ndarray,
    evaluated_track: str = "REAL_DATA_VALIDATION"
) -> None:
    """
    STEP 9 — AUTOMATED BENCHMARK INTEGRITY AND INVALIDITY CHECKS
    
    Detects if:
    1. A synthetic fixture is being presented as REAL_DATA_VALIDATION.
    2. Ground truth is mathematically derived from the exact threshold being evaluated
       (e.g., circular inversion testing).
       
    If any violation is detected: FAILS BENCHMARK VALIDATION immediately.
    """
    # Check 1: Track contamination check
    if evaluated_track == "REAL_DATA_VALIDATION":
        if not sample.is_real_data:
            raise BenchmarkInvalidityError(
                f"FAIL BENCHMARK VALIDATION: Sample '{sample.sample_id}' is marked is_real_data=False "
                f"but was evaluated under REAL_DATA_VALIDATION track."
            )
        if sample.bundle.is_fixture:
            raise BenchmarkInvalidityError(
                f"FAIL BENCHMARK VALIDATION: Sample '{sample.sample_id}' contains a fixture SceneBundle "
                f"(is_fixture=True). Cannot claim REAL_DATA_VALIDATION on fixture assets."
            )

    # Check 2: Mathematical circularity / threshold-inversion detection
    # Checks whether ground_truth is mathematically derived from a common threshold rule on SAR or Optical
    b = sample.bundle
    valid = sample.valid_mask if sample.valid_mask is not None else np.ones_like(sample.ground_truth, dtype=bool)
    
    # Check if ground truth was constructed from sar_vv < threshold
    if hasattr(b, 'post_sar_vv') and b.post_sar_vv is not None:
        # Check standard thresholds
        for test_thresh in [-16.0, -15.5, -17.0, -18.0]:
            candidate_circular_mask = (b.post_sar_vv < test_thresh)[valid]
            gt_valid = sample.ground_truth[valid].astype(bool)
            
            # If 100% of all valid pixels are identical to the evaluated threshold rule AND sample is not verified real data
            if np.array_equal(gt_valid, candidate_circular_mask) and not sample.is_real_data:
                raise BenchmarkInvalidityError(
                    f"FAIL BENCHMARK VALIDATION: Circular threshold generation detected! "
                    f"Ground truth in '{sample.sample_id}' is mathematically identical to (post_sar_vv < {test_thresh} dB)."
                )

    # Check 3: Check if prediction is evaluated against an identical generated mask with zero independent noise
    gt_valid = sample.ground_truth[valid].astype(bool)
    pred_valid = y_pred[valid].astype(bool)
    
    # In real satellite imagery, an IoU of exactly 1.0000 across a 512x512 scene with thousands of water pixels
    # is mathematically anomalous and indicates test set leakage or circular mock data
    if len(gt_valid) > 10000 and np.sum(gt_valid) > 500:
        agreement = np.mean(gt_valid == pred_valid)
        if agreement > 0.9999 and not sample.is_real_data:
            raise BenchmarkInvalidityError(
                f"FAIL BENCHMARK VALIDATION: Anomalous >99.99% agreement on synthetic asset '{sample.sample_id}'. "
                f"Refusing to label result as REAL_DATA_VALIDATION."
            )

def compute_hierarchical_aggregates(
    scene_evaluations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes per-event, per-region, macro-average, and micro-average metrics.
    Guarantees no per-event failure is masked by global aggregation.
    """
    events_map: Dict[str, List[Dict[str, Any]]] = {}
    splits_map: Dict[str, List[Dict[str, Any]]] = {}
    
    # Micro accumulators
    global_tp = 0
    global_fp = 0
    global_fn = 0
    global_tn = 0
    
    for sc in scene_evaluations:
        ev_id = sc["event_id"]
        split = sc["split"]
        
        events_map.setdefault(ev_id, []).append(sc)
        splits_map.setdefault(split, []).append(sc)
        
        m = sc["metrics"]
        global_tp += m["tp"]
        global_fp += m["fp"]
        global_fn += m["fn"]
        global_tn += m["tn"]
        
    per_event: List[Dict[str, Any]] = []
    for ev_id, scenes in events_map.items():
        ious = [s["metrics"]["iou"] for s in scenes]
        f1s = [s["metrics"]["f1"] for s in scenes]
        precs = [s["metrics"]["precision"] for s in scenes]
        recs = [s["metrics"]["recall"] for s in scenes]
        ev_tp = sum(s["metrics"]["tp"] for s in scenes)
        ev_fp = sum(s["metrics"]["fp"] for s in scenes)
        ev_fn = sum(s["metrics"]["fn"] for s in scenes)
        
        per_event.append({
            "event_id": ev_id,
            "event_name": scenes[0]["event_name"],
            "country": scenes[0]["country"],
            "hazard_type": scenes[0]["hazard_type"],
            "split": scenes[0]["split"],
            "sample_count": len(scenes),
            "macro_iou": round(float(np.mean(ious)), 4),
            "macro_f1": round(float(np.mean(f1s)), 4),
            "macro_precision": round(float(np.mean(precs)), 4),
            "macro_recall": round(float(np.mean(recs)), 4),
            "event_micro_iou": round(float(ev_tp / max(1, ev_tp + ev_fp + ev_fn)), 4),
            "scenes": scenes
        })
        
    per_split: Dict[str, Any] = {}
    for split, scenes in splits_map.items():
        ious = [s["metrics"]["iou"] for s in scenes]
        f1s = [s["metrics"]["f1"] for s in scenes]
        precs = [s["metrics"]["precision"] for s in scenes]
        recs = [s["metrics"]["recall"] for s in scenes]
        per_split[split] = {
            "macro_iou": round(float(np.mean(ious)), 4),
            "macro_f1": round(float(np.mean(f1s)), 4),
            "macro_precision": round(float(np.mean(precs)), 4),
            "macro_recall": round(float(np.mean(recs)), 4),
            "sample_count": len(scenes)
        }
        
    micro_iou = float(global_tp / max(1, global_tp + global_fp + global_fn))
    micro_precision = float(global_tp / max(1, global_tp + global_fp))
    micro_recall = float(global_tp / max(1, global_tp + global_fn))
    micro_f1 = float(2 * micro_precision * micro_recall / max(1e-7, micro_precision + micro_recall))
    
    all_ious = [s["metrics"]["iou"] for s in scene_evaluations]
    all_f1s = [s["metrics"]["f1"] for s in scene_evaluations]
    
    return {
        "overall_summary": {
            "macro_iou": round(float(np.mean(all_ious)), 4) if all_ious else 0.0,
            "macro_f1": round(float(np.mean(all_f1s)), 4) if all_f1s else 0.0,
            "micro_iou": round(micro_iou, 4),
            "micro_f1": round(micro_f1, 4),
            "micro_precision": round(micro_precision, 4),
            "micro_recall": round(micro_recall, 4),
            "total_scenes": len(scene_evaluations),
            "total_pixels_evaluated": global_tp + global_fp + global_fn + global_tn
        },
        "per_split_summary": per_split,
        "per_event_evaluations": per_event
    }
