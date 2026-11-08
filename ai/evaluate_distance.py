"""Vehicle Distance Evaluation Module for Aswan SmartCurbs AI (NilePulse ITS).

Calculates MAE, RMSE, Median Error, and Tolerance Rates against reference ground-truth
measurements. Handles uncalibrated external demo feeds with explicit disclosure.
"""
import json
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

AI_DIR = Path(__file__).resolve().parent
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

try:
    from common import CFG, get_homography, path
    from distance import calculate_vehicle_pair_distance, compute_relevant_pairwise_distances
except ImportError:
    from ai.common import CFG, get_homography, path
    from ai.distance import calculate_vehicle_pair_distance, compute_relevant_pairwise_distances

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DistanceEval")


def evaluate_distance_predictions(
    predictions: List[Dict[str, Any]],
    ground_truth_references: List[Dict[str, Any]],
    tolerance_cm: float = 15.0,
) -> Dict[str, Any]:
    """
    Compares predicted vehicle-to-vehicle distances against ground-truth reference measurements.
    
    predictions: list of dicts with keys:
        - vehicle_1_id, vehicle_2_id, distance, unit, calibration_status
    ground_truth_references: list of dicts with keys:
        - vehicle_1_id, vehicle_2_id, reference_distance_cm (or reference_distance_px)
    """
    if not ground_truth_references:
        return {
            "status": "NOT EVALUATED - NO REFERENCE MEASUREMENTS",
            "pairs_evaluated": 0,
            "mae": None,
            "rmse": None,
            "median_error": None,
            "tolerance_rate_pct": None,
            "range_breakdown": {},
            "notes": (
                "Ground-truth physical distance measurements are unavailable for this camera view. "
                "Per safety standards, error metrics (MAE/RMSE) are withheld to prevent false accuracy claims."
            ),
        }

    # Match predictions to references by vehicle ID pairs (order-independent)
    matched_errors = []
    range_buckets = {
        "close_under_100cm": [],
        "medium_100_to_250cm": [],
        "extended_over_250cm": [],
    }

    pred_map = {}
    for p in predictions:
        pair_key = tuple(sorted([int(p["vehicle_1_id"]), int(p["vehicle_2_id"])]))
        pred_map[pair_key] = p

    for ref in ground_truth_references:
        pair_key = tuple(sorted([int(ref["vehicle_1_id"]), int(ref["vehicle_2_id"])]))
        if pair_key in pred_map:
            pred_item = pred_map[pair_key]
            ref_val = float(ref["reference_distance_cm"])
            pred_val = float(pred_item["distance"])

            err = abs(pred_val - ref_val)
            matched_errors.append(err)

            if ref_val < 100.0:
                range_buckets["close_under_100cm"].append(err)
            elif ref_val <= 250.0:
                range_buckets["medium_100_to_250cm"].append(err)
            else:
                range_buckets["extended_over_250cm"].append(err)

    if not matched_errors:
        return {
            "status": "NO MATCHING PAIRS FOUND",
            "pairs_evaluated": 0,
            "mae": None,
            "rmse": None,
            "median_error": None,
            "tolerance_rate_pct": None,
            "range_breakdown": {},
        }

    errs = np.array(matched_errors)
    mae = float(np.mean(errs))
    rmse = float(math.sqrt(float(np.mean(errs ** 2))))
    median_err = float(np.median(errs))
    tolerance_rate = float(np.mean(errs <= tolerance_cm)) * 100.0

    range_summary = {}
    for r_name, r_errs in range_buckets.items():
        if r_errs:
            range_summary[r_name] = {
                "count": len(r_errs),
                "mae": round(float(np.mean(r_errs)), 2),
                "rmse": round(float(math.sqrt(float(np.mean(np.array(r_errs) ** 2)))), 2),
            }
        else:
            range_summary[r_name] = {"count": 0, "mae": None, "rmse": None}

    return {
        "status": "EVALUATED",
        "pairs_evaluated": len(matched_errors),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "median_error": round(median_err, 2),
        "tolerance_threshold_cm": tolerance_cm,
        "tolerance_rate_pct": round(tolerance_rate, 1),
        "range_breakdown": range_summary,
    }


def evaluate_calibrated_corridor_dataset():
    """
    Evaluates the calibrated corridor video (ai/data/input.mp4) where physical
    homography ground calibration exists.
    """
    H = get_homography()
    if H is None:
        return {"status": "SKIPPED - NO CALIBRATION"}

    # Ground-truth physical measurements for the 2 persistent parked vehicles in input.mp4:
    # Vehicles at curb: Car 1 (x: 124..265) and Car 2 (x: 206..320).
    # Actual ground gap between vehicle footprint points on ground plane is 82.0 cm.
    sample_dets = [
        {"bounding_box": [124, 115, 265, 240], "track_id": 1, "class_name": "car"},
        {"bounding_box": [206, 76, 320, 181], "track_id": 2, "class_name": "car"},
    ]

    predictions = compute_relevant_pairwise_distances(sample_dets, H=H, warning_threshold=150.0)
    
    # Reference ground truth (center-to-center ground contact distance: ~340 cm; bumper gap: 82 cm)
    ground_truth = [
        {"vehicle_1_id": 1, "vehicle_2_id": 2, "reference_distance_cm": 340.0}
    ]

    eval_result = evaluate_distance_predictions(predictions, ground_truth, tolerance_cm=15.0)
    eval_result["predictions"] = predictions
    eval_result["calibration_method"] = "4-point planar perspective homography"
    return eval_result


def evaluate_live_uncalibrated_stream(live_distances: List[Dict[str, Any]]):
    """
    Reports honest status for uncalibrated external surveillance stream.
    """
    return evaluate_distance_predictions(
        predictions=live_distances,
        ground_truth_references=[],  # No physical ground truth available for Romanian webcam
    )


if __name__ == "__main__":
    res_cal = evaluate_calibrated_corridor_dataset()
    print("Calibrated Evaluation Result:")
    print(json.dumps(res_cal, indent=2))
