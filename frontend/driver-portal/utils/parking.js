// --------------------------------------------------------------------------
// Shared helpers for the Parking Session / Parking Details roadmap items:
//   - maximum parking duration (parsed from the zone's rules text if the
//     backend doesn't send a dedicated field yet)
//   - elapsed-time formatting for the live session timer
//   - cost estimation (hourlyRate * elapsed time)
// --------------------------------------------------------------------------

/**
 * Resolve the maximum stay, in minutes, for a zone.
 * Prefers an explicit `max_duration_minutes` field from the backend/mock
 * data; falls back to parsing text like "Maximum stay: 2 hours" out of the
 * zone's `rules` string so this still works against zones that only carry
 * free-text rules.
 */
export function parseMaxDurationMinutes(rules, explicitMinutes) {
  if (explicitMinutes !== undefined && explicitMinutes !== null) {
    return explicitMinutes;
  }
  if (!rules) return null;

  const match = String(rules).match(/max(?:imum)?\s*stay[:\s]*([\d.]+)\s*(hour|hr|minute|min)/i);
  if (!match) return null;

  const value = parseFloat(match[1]);
  if (Number.isNaN(value)) return null;

  const unit = match[2].toLowerCase();
  return unit.startsWith("h") ? Math.round(value * 60) : Math.round(value);
}

/** "Not specified" | "45 min" | "2 hours" | "1.5 hours" */
export function formatDuration(minutes) {
  if (minutes === null || minutes === undefined) return "No fixed limit";
  if (minutes <= 0) return "No fixed limit";
  if (minutes < 60) return `${minutes} min`;
  const hours = minutes / 60;
  const hoursLabel = Number.isInteger(hours) ? hours : hours.toFixed(1);
  return `${hoursLabel} hour${hours === 1 ? "" : "s"}`;
}

/** milliseconds -> "HH:MM:SS" */
export function formatElapsed(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

/** hourlyRate (EGP) * elapsed time -> cost in EGP, rounded to 2 decimals */
export function computeCost(hourlyRate, elapsedMs) {
  if (!hourlyRate || elapsedMs <= 0) return 0;
  const hours = elapsedMs / 3600000;
  return Math.round(hourlyRate * hours * 100) / 100;
}

/** ISO timestamp -> "3:45 PM" (falls back gracefully) */
export function formatClockTime(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

/** ISO timestamp -> "24 Sep 2026" */
export function formatShortDate(iso) {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" });
}

/** Haversine distance between two lat/lng points, in kilometers. */
export function haversineDistanceKm(lat1, lon1, lat2, lon2) {
  if ([lat1, lon1, lat2, lon2].some((v) => v === null || v === undefined || Number.isNaN(Number(v)))) {
    return null;
  }
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/** km -> "850 m away" | "1.4 km away" */
export function formatDistance(km) {
  if (km === null || km === undefined || Number.isNaN(km)) return null;
  if (km < 1) return `${Math.max(1, Math.round(km * 1000))} m away`;
  return `${km.toFixed(1)} km away`;
}
