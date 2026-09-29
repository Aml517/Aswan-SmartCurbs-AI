// --------------------------------------------------------------------------
// Aswan SmartCurbs AI — Driver Portal local history store
//
// Implements roadmap sections 4.3 (Parking Session) and 4.5 (User History).
// The backend does not expose dedicated /sessions, /payments, /receipts or
// /violations endpoints yet (see backend/app/api/v1/*.py — only zones,
// availability and reservations exist today). Rather than block the User
// Portal roadmap on backend work, this module keeps that data per-browser
// in localStorage, in the exact shape the History page and API layer
// expect, so it's a drop-in swap for real endpoints later: replace the
// bodies of the functions below with `apiClient` calls and nothing else in
// the app needs to change.
// --------------------------------------------------------------------------

const KEYS = {
  reservations: "smartcurbs_history_reservations",
  sessions: "smartcurbs_history_sessions",
  payments: "smartcurbs_history_payments",
  receipts: "smartcurbs_history_receipts",
  violations: "smartcurbs_history_violations",
};

function readList(key) {
  try {
    const raw = localStorage.getItem(key);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeList(key, list) {
  try {
    localStorage.setItem(key, JSON.stringify(list));
  } catch {
    // Storage unavailable (private mode, quota, etc.) — fail silently,
    // the portal still works, it just won't remember history this visit.
  }
}

let idSeed = Date.now();
function nextId(prefix) {
  idSeed += 1;
  return `${prefix}-${idSeed.toString(36)}`;
}

// ---- Reservations ---------------------------------------------------------

/** Log a reservation the driver just made, for the History → Reservations tab. */
export function recordReservation(entry) {
  const list = readList(KEYS.reservations);
  const record = { id: nextId("res"), createdAt: new Date().toISOString(), ...entry };
  list.unshift(record);
  writeList(KEYS.reservations, list);
  return record;
}

export function getReservationHistory() {
  return readList(KEYS.reservations);
}

// ---- Parking sessions -------------------------------------------------------

/**
 * Start a live parking session for a just-made (paid) reservation.
 * Returns the session record; elapsed time/cost are derived from
 * `startedAt` by the caller so the timer survives page refreshes.
 */
export function startSession({
  reservationId,
  zoneId,
  zoneName,
  zoneType,
  spaceNumber,
  hourlyRate,
  maxDurationMinutes,
  driverName,
  plateNumber,
}) {
  const list = readList(KEYS.sessions);
  const session = {
    id: nextId("sess"),
    reservationId: reservationId ?? null,
    zoneId,
    zoneName,
    zoneType: zoneType || "PAID",
    spaceNumber: spaceNumber ?? null,
    hourlyRate: hourlyRate ?? 0,
    maxDurationMinutes: maxDurationMinutes ?? null,
    driverName: driverName || null,
    plateNumber: plateNumber || null,
    status: "active",
    startedAt: new Date().toISOString(),
    endedAt: null,
    finalCost: null,
  };
  list.unshift(session);
  writeList(KEYS.sessions, list);
  return session;
}

export function getSession(sessionId) {
  return readList(KEYS.sessions).find((session) => session.id === sessionId) || null;
}

export function getSessionHistory() {
  return readList(KEYS.sessions);
}

/**
 * End an active session: marks it completed, stores the final cost, and —
 * when there's a charge — generates the matching payment + receipt records
 * (History → Payments / Receipts tabs).
 */
export function endSession(sessionId, finalCost) {
  const list = readList(KEYS.sessions);
  const index = list.findIndex((session) => session.id === sessionId);
  if (index === -1) return null;

  const endedAt = new Date().toISOString();
  const roundedCost = Math.round((finalCost || 0) * 100) / 100;
  list[index] = { ...list[index], status: "completed", endedAt, finalCost: roundedCost };
  writeList(KEYS.sessions, list);
  const session = list[index];

  if (roundedCost > 0) {
    const payment = {
      id: nextId("pay"),
      sessionId,
      zoneName: session.zoneName,
      amount: roundedCost,
      method: "In-app payment",
      status: "paid",
      createdAt: endedAt,
    };
    const payments = readList(KEYS.payments);
    payments.unshift(payment);
    writeList(KEYS.payments, payments);

    const receipt = {
      id: nextId("rcpt"),
      sessionId,
      paymentId: payment.id,
      zoneName: session.zoneName,
      spaceNumber: session.spaceNumber,
      plateNumber: session.plateNumber,
      amount: roundedCost,
      startedAt: session.startedAt,
      endedAt,
      createdAt: endedAt,
    };
    const receipts = readList(KEYS.receipts);
    receipts.unshift(receipt);
    writeList(KEYS.receipts, receipts);
  }

  return session;
}

export function getPaymentHistory() {
  return readList(KEYS.payments);
}

export function getReceiptHistory() {
  return readList(KEYS.receipts);
}

// ---- Violations -------------------------------------------------------------
// No AI enforcement pipeline is wired up yet (see roadmap section 6/9), so
// this always starts empty. Kept as a first-class list so the History page
// already has the right shape once AI-assisted violations land.

export function getViolationHistory() {
  return readList(KEYS.violations);
}
