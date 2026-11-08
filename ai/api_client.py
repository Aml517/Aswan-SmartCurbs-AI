"""Push occupancy changes to the Slotiq backend: POST /api/v1/occupancy (only stable changes are sent)."""
import json
import urllib.request

from common import CFG


class OccupancyPublisher:
    def __init__(self, cfg=CFG):
        b = cfg.get("backend", {})
        self.enabled = bool(b.get("enabled", False))
        api_base = b.get("api_base") or b.get("url") or "http://127.0.0.1:8001/api/v1"
        self.base = str(api_base).rstrip("/")
        self.zone_id = int(b.get("zone_id", 1))
        self.map = b.get("space_map", {"1": 1, "2": 2})
        thresholds = cfg.get("thresholds", {})
        self.stable = int(thresholds.get("stable_frames", 3))
        self.state, self.pending = {}, {}
        self.updates_sent = 0

    def update(self, space_id, ai_status, confidence=1.0):
        """Call once per frame per space. Sends only after the new status persisted `stable` frames."""
        status = "occupied" if ai_status == "Occupied" else "available"
        current = self.state.setdefault(space_id, "available")   # database default
        if status == current:
            self.pending[space_id] = 0
            return
        self.pending[space_id] = self.pending.get(space_id, 0) + 1
        if self.pending[space_id] >= self.stable:
            self.state[space_id], self.pending[space_id] = status, 0
            self.send(space_id, status, confidence)

    def send(self, space_id, status, confidence):
        backend_id = self.map.get(str(space_id))
        if not self.enabled or backend_id is None:
            return False
        body = json.dumps({"zone_id": self.zone_id, "space_id": backend_id, "status": status, "confidence": confidence}).encode()
        req = urllib.request.Request(f"{self.base}/occupancy", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=3).read()
            self.updates_sent += 1
            return True
        except Exception as e:
            print(f"[api] could not send update for space {space_id}: {e}")
            return False
