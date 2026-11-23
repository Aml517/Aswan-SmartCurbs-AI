"""Offline tests for the AI -> Backend integration (no model, no video, no running backend needed).

Run from the ai/ folder:   python -m unittest discover -s tests -v
"""
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api_client import OccupancyPublisher            # noqa: E402
from common import CFG, load_json, normalize_polygon, polygon_is_simple   # noqa: E402
from contracts import frame_message, validate_zone_payload, zone_payload  # noqa: E402
from occupancy import PARKING_SPACES, calculate_frame_occupancy          # noqa: E402

BOWTIE = [(171, 242), (254, 218), (144, 145), (263, 184)]      # the old, wrong order of space 1


def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def vehicle(track_id, point, conf=0.9):
    x, y = point
    return {"track_id": track_id, "class_name": "car", "confidence": conf,
            "bounding_box": [int(x - 40), int(y - 30), int(x + 40), int(y + 30)], "center_x": x, "center_y": y}


class PolygonTests(unittest.TestCase):
    def test_bowtie_is_detected_and_fixed(self):
        self.assertFalse(polygon_is_simple(BOWTIE))
        self.assertTrue(polygon_is_simple(normalize_polygon(BOWTIE)))

    def test_all_configured_spaces_are_simple(self):
        for sid, poly in PARKING_SPACES.items():
            self.assertTrue(polygon_is_simple(poly), f"space {sid}")

    def test_parking_spaces_json_is_simple(self):
        for item in load_json(Path(__file__).resolve().parents[1] / "parking_spaces.json"):
            self.assertTrue(polygon_is_simple([tuple(p) for p in item["points"]]), f"space {item['id']}")


class OccupancyScenarioTests(unittest.TestCase):
    """A car arrives, parks, leaves; and a car just drives past - the video input.mp4 never does this."""

    def test_enter_park_leave(self):
        c1 = centroid(PARKING_SPACES[1])
        timeline = []
        for f in range(100):
            dets = [vehicle(7, c1)] if 20 <= f < 60 else []
            timeline.append(calculate_frame_occupancy(dets)[1]["status"])
        self.assertEqual(timeline[:20], ["Free"] * 20)
        self.assertEqual(timeline[20:60], ["Occupied"] * 40)
        self.assertEqual(timeline[60:], ["Free"] * 40)
        flips = sum(1 for a, b in zip(timeline, timeline[1:]) if a != b)
        self.assertEqual(flips, 2)

    def test_vehicle_outside_any_space_changes_nothing(self):
        spaces = calculate_frame_occupancy([vehicle(9, (600, 300))])
        self.assertTrue(all(s["status"] == "Free" for s in spaces.values()))

    def test_each_space_has_one_state_and_best_vehicle_wins(self):
        c1 = centroid(PARKING_SPACES[1])
        spaces = calculate_frame_occupancy([vehicle(1, c1, 0.5), vehicle(2, c1, 0.9)])
        self.assertEqual(spaces[1]["vehicle_id"], 2)


class _Recorder(OccupancyPublisher):
    def __init__(self):
        super().__init__({"backend": {"enabled": True, "zone_id": 1, "space_map": {"1": 1, "2": 2}},
                          "thresholds": {"stable_frames": 3}})
        self.sent = []

    def send(self, space_id, status, confidence):
        self.sent.append((space_id, status))
        return True


class StabilityTests(unittest.TestCase):
    def test_single_frame_blips_are_ignored(self):
        p = _Recorder()
        for st in ["Free", "Occupied", "Free", "Occupied", "Free", "Free"]:
            p.update(1, st)
        self.assertEqual(p.sent, [])

    def test_stable_change_is_sent_once(self):
        p = _Recorder()
        for st in ["Free", "Occupied", "Occupied", "Occupied", "Occupied", "Occupied"]:
            p.update(1, st)
        self.assertEqual(p.sent, [(1, "occupied")])


class ContractTests(unittest.TestCase):
    def test_frame_message_shape(self):
        m = frame_message(120, [vehicle(15, (200, 145), 0.94)], fps=30)
        self.assertEqual(set(m), {"frame_id", "timestamp", "vehicles"})
        self.assertEqual(m["timestamp"], 4.0)
        self.assertEqual(set(m["vehicles"][0]), {"track_id", "class", "confidence", "bbox"})

    def test_zone_payload_is_valid_and_counts_match(self):
        spaces = {1: {"status": "Occupied", "vehicle_id": 15, "confidence": 0.94},
                  2: {"status": "Free", "vehicle_id": None, "confidence": None}}
        p = zone_payload(1, spaces, {"1": 3, "2": 4})
        self.assertEqual(validate_zone_payload(p), [])
        self.assertEqual((p["occupied_count"], p["available_count"], p["occupancy_percentage"]), (1, 1, 50))
        self.assertEqual([i["space_id"] for i in p["occupancy"]], [3, 4])
        self.assertIsNone(p["occupancy"][1]["track_id"])

    def test_validator_catches_bad_payloads(self):
        bad = {"zone_id": 1, "occupancy": [{"space_id": 3, "status": "occupied", "track_id": None},
                                           {"space_id": 3, "status": "free", "track_id": None}],
               "occupied_count": 0, "available_count": 0, "occupancy_percentage": 0}
        self.assertGreaterEqual(len(validate_zone_payload(bad)), 3)


class PublishZoneTests(unittest.TestCase):
    """publish_zone() talks to a tiny local server that mimics POST /api/v1/occupancy."""

    def setUp(self):
        received = self.received = []

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *a):
                pass

        self.srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.pub = OccupancyPublisher({"backend": {"enabled": True, "zone_id": 1,
                                                   "api_base": f"http://127.0.0.1:{self.srv.server_port}/api/v1",
                                                   "space_map": {"1": 3, "2": 4}}})

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()

    def test_only_changes_are_posted_and_body_matches_backend_schema(self):
        occupied = {1: {"status": "Occupied", "vehicle_id": 15, "confidence": 0.94},
                    2: {"status": "Free", "vehicle_id": None, "confidence": None}}
        payload = zone_payload(1, occupied, {"1": 3, "2": 4})
        self.assertEqual(self.pub.publish_zone(payload), [3])           # space 4 is still 'available' -> not sent
        self.assertEqual(self.pub.publish_zone(payload), [])            # same state again -> nothing sent
        path, body = self.received[0]
        self.assertEqual(path, "/api/v1/occupancy")
        self.assertEqual(body, {"zone_id": 1, "space_id": 3, "status": "occupied", "confidence": 0.94})
        freed = zone_payload(1, {1: {"status": "Free", "vehicle_id": None, "confidence": None},
                                 2: {"status": "Free", "vehicle_id": None, "confidence": None}}, {"1": 3, "2": 4})
        self.assertEqual(self.pub.publish_zone(freed), [3])
        self.assertEqual(self.received[1][1]["status"], "available")

    def test_invalid_payload_is_refused(self):
        with self.assertRaises(ValueError):
            self.pub.publish_zone({"zone_id": 1, "occupancy": [{"space_id": 3, "status": "busy", "track_id": None}],
                                   "occupied_count": 0, "available_count": 1, "occupancy_percentage": 0})


if __name__ == "__main__":
    unittest.main()
