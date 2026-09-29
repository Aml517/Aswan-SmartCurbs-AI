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

import { completeReservation } from "./api";

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
  const record = {
    id: entry.reservationId ? `res-${entry.reservationId}` : nextId("res"),
    createdAt: new Date().toISOString(),
    ...entry,
  };
  
  // Deduplicate by reservationId
  const existingIndex = list.findIndex(
    (r) => (entry.reservationId && r.reservationId === entry.reservationId) || r.id === record.id
  );
  if (existingIndex >= 0) {
    list[existingIndex] = { ...list[existingIndex], ...record };
  } else {
    list.unshift(record);
  }
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
 * Also marks the initiating reservation as COMPLETED and frees the space.
 */
export async function endSession(sessionId, finalCost) {
  const list = readList(KEYS.sessions);
  const index = list.findIndex((session) => session.id === sessionId);
  if (index === -1) return null;

  const endedAt = new Date().toISOString();
  const roundedCost = Math.round((finalCost || 0) * 100) / 100;
  list[index] = { ...list[index], status: "completed", endedAt, finalCost: roundedCost };
  writeList(KEYS.sessions, list);
  const session = list[index];

  // 1. Update the associated reservation in history to COMPLETED
  if (session.reservationId) {
    const resList = readList(KEYS.reservations);
    const resIndex = resList.findIndex(
      (r) => r.reservationId === session.reservationId || r.id === `res-${session.reservationId}` || r.id === session.reservationId
    );
    if (resIndex >= 0) {
      resList[resIndex] = { ...resList[resIndex], status: "completed" };
      writeList(KEYS.reservations, resList);
    }

    // 2. Call backend API to mark reservation completed and release space
    try {
      await completeReservation(session.reservationId);
    } catch (err) {
      console.warn("Backend reservation completion notice:", err?.message || err);
    }
  }

  // 3. Create or update exactly one payment record
  if (roundedCost > 0) {
    const payment = {
      id: nextId("pay"),
      sessionId,
      reservationId: session.reservationId ?? null,
      zoneName: session.zoneName,
      amount: roundedCost,
      method: "In-app payment",
      status: "paid",
      createdAt: endedAt,
    };
    const payments = readList(KEYS.payments);
    // Replace if same session already existed, otherwise unshift
    const existingPayIdx = payments.findIndex((p) => p.sessionId === sessionId);
    if (existingPayIdx >= 0) {
      payments[existingPayIdx] = payment;
    } else {
      payments.unshift(payment);
    }
    writeList(KEYS.payments, payments);

    // 4. Create exactly one receipt record
    const receipt = {
      id: nextId("rcpt"),
      sessionId,
      paymentId: payment.id,
      reservationId: session.reservationId ?? null,
      zoneName: session.zoneName,
      spaceNumber: session.spaceNumber,
      plateNumber: session.plateNumber,
      amount: roundedCost,
      startedAt: session.startedAt,
      endedAt,
      createdAt: endedAt,
    };
    const receipts = readList(KEYS.receipts);
    const existingRcptIdx = receipts.findIndex((r) => r.sessionId === sessionId);
    if (existingRcptIdx >= 0) {
      receipts[existingRcptIdx] = receipt;
    } else {
      receipts.unshift(receipt);
    }
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
