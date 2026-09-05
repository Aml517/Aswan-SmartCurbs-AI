// Mock data for the Driver Portal — shaped to mirror the REAL FastAPI backend
// contract exactly (see backend/app/schemas/*.py). This is only used when
// VITE_USE_MOCK_DATA=true (e.g. presenting without the backend running).
// Field names deliberately match the backend's snake_case so the mock and
// live paths in services/api.js can share the same normalization code.

let nextSpaceId = 1;

function buildSpaces(zoneId, prefix, counts) {
  const spaces = [];
  let n = 1;

  for (let i = 0; i < counts.available; i++, n++) {
    spaces.push({ id: nextSpaceId++, zone_id: zoneId, space_number: `${prefix}${n}`, status: "available" });
  }
  for (let i = 0; i < counts.occupied; i++, n++) {
    spaces.push({ id: nextSpaceId++, zone_id: zoneId, space_number: `${prefix}${n}`, status: "occupied" });
  }
  for (let i = 0; i < counts.reserved; i++, n++) {
    spaces.push({ id: nextSpaceId++, zone_id: zoneId, space_number: `${prefix}${n}`, status: "reserved" });
  }
  return spaces;
}

export const mockZones = [
  {
    id: 1,
    name: "Zone A - Corniche",
    location: "Corniche El Nile St, Aswan",
    total_spaces: 50,
    latitude: 24.0889,
    longitude: 32.8998,
    created_at: "2026-08-01T09:00:00+02:00",
    spaces: buildSpaces(1, "A", { available: 18, occupied: 27, reserved: 5 }),
  },
  {
    id: 2,
    name: "Zone B - Souk El Souq",
    location: "El Souq St, Aswan",
    total_spaces: 30,
    latitude: 24.0912,
    longitude: 32.8991,
    created_at: "2026-08-01T09:00:00+02:00",
    spaces: buildSpaces(2, "B", { available: 13, occupied: 14, reserved: 3 }),
  },
  {
    id: 3,
    name: "Zone C - Aswan Train Station",
    location: "Station Square, Aswan",
    total_spaces: 40,
    latitude: 24.0947,
    longitude: 32.9021,
    created_at: "2026-08-01T09:00:00+02:00",
    spaces: buildSpaces(3, "C", { available: 8, occupied: 28, reserved: 4 }),
  },
];

export const mockReservations = [];
