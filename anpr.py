"""ANPR prototype (Word doc 5.4): vehicle -> plate crop -> OCR -> plate number -> session / zone event.

Optional: needs `pip install easyocr` and config.json -> anpr.enabled = true. Without a dedicated plate detector
the plate is searched in the lower part of the vehicle box, so accuracy is limited (prototype).
"""
import re

import cv2

from common import CFG


class PlateReader:
    def __init__(self):
        self.reader = None
        try:
            import easyocr
            self.reader = easyocr.Reader(["ar", "en"], gpu=False)   # Egyptian plates use Arabic + digits
        except ImportError:
            print("[anpr] easyocr not installed -> ANPR disabled (pip install easyocr)")

    def read(self, frame, bbox):
        if self.reader is None:
            return None
        x1, y1, x2, y2 = bbox
        crop = frame[int(y1 + 0.55 * (y2 - y1)):y2, x1:x2]
        if crop.size == 0:
            return None
        best = None
        for _, text, conf in self.reader.readtext(crop):
            text = re.sub(r"\s+", "", text)
            if len(text) >= 4 and (best is None or conf > best[1]):
                best = (text, float(conf))
        return best


def attach_plates(all_detections, video_path, every_n=None):
    """Read plates every N frames; keep the best reading per track and write it into every detection."""
    every_n = every_n or CFG["anpr"]["every_n_frames"]
    reader = PlateReader()
    if reader.reader is None:
        return all_detections
    cap = cv2.VideoCapture(str(video_path))
    best = {}
    for i, dets in enumerate(all_detections):
        ok, frame = cap.read()
        if not ok:
            break
        if i % every_n:
            continue
        for d in dets:
            r = reader.read(frame, d["bounding_box"])
            if r and (d["track_id"] not in best or r[1] > best[d["track_id"]][1]):
                best[d["track_id"]] = r
    cap.release()
    for dets in all_detections:
        for d in dets:
            if d["track_id"] in best:
                d["plate"], d["plate_confidence"] = best[d["track_id"]]
    return all_detections
