"""Push occupancy changes to the Slotiq backend: POST /api/v1/occupancy (only stable changes are sent)."""
import json
import urllib.request

from common import CFG


class OccupancyPublisher:
    def __init__(self, cfg=CFG):
        b = cfg["backend"]
        self.enabled, self.base, self.zone_id, self.map = b["enabled"], b["api_base"].rstrip("/"), b["zone_id"], b["space_map"]
        self.stable = cfg["thresholds"]["stable_frames"]
        self.state, self.pending = {}, {}

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
            return True
        except Exception as e:
            print(f"[api] could not send update for space {space_id}: {e}")
            return False
