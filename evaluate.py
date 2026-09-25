"""Detection accuracy against manual ground truth (made with create_ground_truth.py).

Only the annotated frames are evaluated. Ground-truth frame numbers are 0-based, tracking frame_number is
1-based, so ground-truth frame N is all_detections[N].
"""
from common import iou, load_json


def evaluate_detection(all_detections, gt_path, iou_threshold=0.45):
    gt = load_json(gt_path)
    tp = fp = fn = 0
    for ann in gt["annotations"]:
        n = ann["frame_number"]
        preds = sorted(all_detections[n] if n < len(all_detections) else [], key=lambda d: -d["confidence"])
        truths, used = ann["objects"], set()
        for p in preds:
            best, best_iou = None, 0.0
            for i, g in enumerate(truths):
                score = iou(p["bounding_box"], g["bounding_box"])
                if i not in used and score > best_iou:
                    best, best_iou = i, score
            if best is not None and best_iou >= iou_threshold:
                tp += 1; used.add(best)
            else:
                fp += 1
        fn += len(truths) - len(used)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"frames_evaluated": len(gt["annotations"]), "iou_threshold": iou_threshold, "tp": tp, "fp": fp, "fn": fn,
            "precision": precision, "recall": recall}
