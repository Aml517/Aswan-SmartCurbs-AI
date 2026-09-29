import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import { getSession, endSession } from "../services/localHistory";
import { formatElapsed, formatDuration, computeCost, formatClockTime } from "../utils/parking";
import "./ParkingSession.css";

// User Portal roadmap 4.3 — Parking Session:
// Start session (done from Reservation.jsx) → live timer → elapsed
// duration → estimated/current cost → overstay warning → End session →
// final cost + receipt.

export default function ParkingSession() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(() => getSession(sessionId));
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    setSession(getSession(sessionId));
  }, [sessionId]);

  useEffect(() => {
    if (!session || session.status !== "active") return undefined;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [session]);

  const elapsedMs = session ? now - new Date(session.startedAt).getTime() : 0;

  const isOverstay =
    !!session &&
    session.status === "active" &&
    !!session.maxDurationMinutes &&
    elapsedMs / 60000 > session.maxDurationMinutes;

  const currentCost = useMemo(
    () => (session ? computeCost(session.hourlyRate, elapsedMs) : 0),
    [session, elapsedMs]
  );

  if (!session) {
    return (
      <div className="page-container">
        <EmptyState
          title="Session not found"
          message="This parking session may have already ended, or the link is invalid."
          actionLabel="Back to zones"
          onAction={() => navigate("/parking-zones")}
        />
      </div>
    );
  }

  async function handleEndSession() {
    const finalElapsedMs = Math.max(0, Date.now() - new Date(session.startedAt).getTime());
    const finalCost = computeCost(session.hourlyRate, finalElapsedMs);
    const updated = await endSession(session.id, finalCost);
    setSession(updated);
  }

  const isActive = session.status === "active";
  const finalDurationMs = session.endedAt
    ? new Date(session.endedAt).getTime() - new Date(session.startedAt).getTime()
    : 0;

  return (
    <div className="page-container">
      <Link to={`/parking-zones/${session.zoneId}`} className="details-back">
        ← Back to {session.zoneName}
      </Link>

      <div className="session-card surface">
        <div className="session-header">
          <div>
            <span className="eyebrow">
              {isActive ? "Parking Session In Progress" : "Parking Session Ended"}
            </span>
            <h1>{session.zoneName}</h1>
            <p className="session-meta">
              Space {session.spaceNumber || "—"} · {session.plateNumber || "No plate on file"}
            </p>
          </div>
          <span className={`pill ${isActive ? "pill-open" : "pill-session-done"}`}>
            {isActive ? "Active" : "Completed"}
          </span>
        </div>

        {isActive ? (
          <>
            <div className="session-timer">
              <span className="session-timer-value">{formatElapsed(elapsedMs)}</span>
              <span className="session-timer-label">Elapsed Time</span>
            </div>

            <dl className="session-stats">
              <div>
                <dt>Started At</dt>
                <dd>{formatClockTime(session.startedAt)}</dd>
              </div>
              <div>
                <dt>Max Stay</dt>
                <dd>{formatDuration(session.maxDurationMinutes)}</dd>
              </div>
              <div>
                <dt>Rate</dt>
                <dd>{session.hourlyRate ? `${session.hourlyRate} EGP/hr` : "Free"}</dd>
              </div>
              <div>
                <dt>Estimated Cost</dt>
                <dd className="session-cost">{currentCost.toFixed(2)} EGP</dd>
              </div>
            </dl>

            {isOverstay && (
              <div className="restriction-callout session-overstay">
                <div className="restriction-callout-header">
                  <span aria-hidden="true">⚠️</span>
                  <span>Overstay Warning</span>
                </div>
                <p>
                  You've exceeded the maximum stay of {formatDuration(session.maxDurationMinutes)} for
                  this zone. Additional charges may apply and the vehicle may be flagged for an overstay
                  violation — please end your session or move your vehicle.
                </p>
              </div>
            )}

            <button type="button" className="btn btn-primary btn-block" onClick={handleEndSession}>
              End Session
            </button>
          </>
        ) : (
          <>
            <div className="session-receipt">
              <div className="session-receipt-total">
                <span className="session-receipt-total-value">
                  {Number(session.finalCost || 0).toFixed(2)} EGP
                </span>
                <span className="session-receipt-total-label">Final Cost</span>
              </div>

              <dl className="session-stats">
                <div>
                  <dt>Started</dt>
                  <dd>{formatClockTime(session.startedAt)}</dd>
                </div>
                <div>
                  <dt>Ended</dt>
                  <dd>{formatClockTime(session.endedAt)}</dd>
                </div>
                <div>
                  <dt>Duration</dt>
                  <dd>{formatElapsed(finalDurationMs)}</dd>
                </div>
                <div>
                  <dt>Payment</dt>
                  <dd className={session.finalCost > 0 ? "session-cost" : ""}>
                    {session.finalCost > 0 ? "Paid — In-app payment" : "No charge"}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="details-action-group">
              <button type="button" className="btn btn-secondary btn-block" onClick={() => navigate("/history")}>
                View Full History
              </button>
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={() => navigate("/parking-zones")}
              >
                Browse Other Zones
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
