"""Interactive calibration so distances are reported in centimetres (Word doc 5.2).

1) Click 4 ground points forming a rectangle of KNOWN size (e.g. a marked bay): top-left, top-right, bottom-right, bottom-left.
2) Enter the rectangle width and length in cm.
3) Click 2 points on the curb line (or press S to skip).
Saved to config.json -> calibration + curb_line. Keys: R = reset points, Q = quit without saving.
"""
import cv2

from common import CFG, path, save_config


def collect(frame, count, title):
    pts, canvas = [], frame.copy()

    def click(event, x, y, *_):
        if event == cv2.EVENT_LBUTTONDOWN and len(pts) < count:
            pts.append([x, y]); cv2.circle(canvas, (x, y), 5, (0, 255, 0), -1); cv2.imshow(title, canvas)

    cv2.namedWindow(title); cv2.setMouseCallback(title, click); cv2.imshow(title, canvas)
    while len(pts) < count:
        k = cv2.waitKey(20) & 0xFF
        if k == ord("q"):
            cv2.destroyAllWindows(); raise SystemExit("Cancelled.")
        if k == ord("s") and count == 2:
            break
        if k == ord("r"):
            pts.clear(); canvas[:] = frame; cv2.imshow(title, canvas)
    cv2.destroyWindow(title)
    return pts


def main():
    cap = cv2.VideoCapture(str(path(CFG["video"])))
    ok, frame = cap.read(); cap.release()
    if not ok:
        raise SystemExit("Could not read the video frame.")
    ground = collect(frame, 4, "1) Click 4 ground points (TL, TR, BR, BL) of a known rectangle")
    width = float(input("Rectangle width in cm (left-right): "))
    length = float(input("Rectangle length in cm (top-bottom): "))
    curb = collect(frame, 2, "2) Click 2 points on the curb line (S = skip)")
    cfg = dict(CFG)
    cfg["calibration"] = {"enabled": True, "image_points": ground, "world_points_cm": [[0, 0], [width, 0], [width, length], [0, length]]}
    cfg["curb_line"] = {"p1": curb[0], "p2": curb[1]} if len(curb) == 2 else None
    save_config(cfg)
    print("Calibration saved to config.json. Distances will now be reported in cm.")


if __name__ == "__main__":
    main()
