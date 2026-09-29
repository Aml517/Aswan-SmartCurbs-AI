import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import {
  getReservationHistory,
  getSessionHistory,
  getPaymentHistory,
  getReceiptHistory,
  getViolationHistory,
} from "../services/localHistory";
import { formatClockTime, formatShortDate, formatElapsed } from "../utils/parking";
import "./History.css";

// User Portal roadmap 4.5 — User History. Sections match the roadmap
// exactly: Reservations, Parking Sessions, Payments, Receipts, Violations.
const TABS = [
  { key: "reservations", label: "Reservations" },
  { key: "sessions", label: "Parking Sessions" },
  { key: "payments", label: "Payments" },
  { key: "receipts", label: "Receipts" },
  { key: "violations", label: "Violations" },
];

function StatusPill({ status }) {
  const normalized = (status || "").toLowerCase();
  const map = {
    active: { key: "open", label: "Active" },
    completed: { key: "session-done", label: "Completed" },
    paid: { key: "session-done", label: "Paid" },
    cancelled: { key: "restricted", label: "Cancelled" },
  };
  const info = map[normalized] || { key: "limited", label: status || "Unknown" };
  return <span className={`pill pill-${info.key}`}>{info.label}</span>;
}

export default function History() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("reservations");

  // Local history is per-browser (see services/localHistory.js), so it's
  // read fresh whenever this page mounts / a new record is written.
  const reservations = useMemo(() => getReservationHistory(), [activeTab]);
  const sessions = useMemo(() => getSessionHistory(), [activeTab]);
  const payments = useMemo(() => getPaymentHistory(), [activeTab]);
  const receipts = useMemo(() => getReceiptHistory(), [activeTab]);
  const violations = useMemo(() => getViolationHistory(), [activeTab]);

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="eyebrow">Driver Portal</span>
        <h1>My History</h1>
        <p>Reservations, parking sessions, payments, receipts and violations tied to your account.</p>
      </div>

      <div className="history-tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`history-tab ${activeTab === tab.key ? "history-tab-active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "reservations" && (
        <div className="history-list">
          {reservations.length === 0 ? (
            <EmptyState
              title="No reservations yet"
              message="Reservations you make will show up here — upcoming, active and previous."
              actionLabel="Browse parking zones"
              onAction={() => navigate("/parking-zones")}
            />
          ) : (
            reservations.map((r) => (
              <article key={r.id} className="history-row surface">
                <div className="history-row-main">
                  <h3>{r.zoneName}</h3>
                  <p className="history-row-sub">
                    Space {r.spaceNumber} · {r.zoneType === "FREE" ? "Free zone" : `${r.hourlyRate ?? "—"} EGP/hr`}
                  </p>
                  <p className="history-row-sub">
                    {formatShortDate(r.startTime)} · {formatClockTime(r.startTime)}
                    {r.endTime ? ` – ${formatClockTime(r.endTime)}` : ""}
                  </p>
                </div>
                <StatusPill status={r.status} />
              </article>
            ))
          )}
        </div>
      )}

      {activeTab === "sessions" && (
        <div className="history-list">
          {sessions.length === 0 ? (
            <EmptyState
              title="No parking sessions yet"
              message="Start a session from a paid reservation to track live time and cost here."
              actionLabel="Browse parking zones"
              onAction={() => navigate("/parking-zones")}
            />
          ) : (
            sessions.map((s) => (
              <article
                key={s.id}
                className="history-row surface history-row-clickable"
                onClick={() => navigate(`/session/${s.id}`)}
              >
                <div className="history-row-main">
                  <h3>{s.zoneName}</h3>
                  <p className="history-row-sub">
                    Space {s.spaceNumber || "—"} · Started {formatClockTime(s.startedAt)} on{" "}
                    {formatShortDate(s.startedAt)}
                  </p>
                  <p className="history-row-sub">
                    {s.status === "completed"
                      ? `Duration ${formatElapsed(new Date(s.endedAt) - new Date(s.startedAt))} · ${Number(
                          s.finalCost || 0
                        ).toFixed(2)} EGP`
                      : "In progress"}
                  </p>
                </div>
                <StatusPill status={s.status} />
              </article>
            ))
          )}
        </div>
      )}

      {activeTab === "payments" && (
        <div className="history-list">
          {payments.length === 0 ? (
            <EmptyState
              title="No payments yet"
              message="Payments from completed paid parking sessions will appear here."
            />
          ) : (
            payments.map((p) => (
              <article key={p.id} className="history-row surface">
                <div className="history-row-main">
                  <h3>{p.zoneName}</h3>
                  <p className="history-row-sub">
                    {p.method} · {formatShortDate(p.createdAt)} at {formatClockTime(p.createdAt)}
                  </p>
                </div>
                <div className="history-row-amount">{Number(p.amount).toFixed(2)} EGP</div>
              </article>
            ))
          )}
        </div>
      )}

      {activeTab === "receipts" && (
        <div className="history-list">
          {receipts.length === 0 ? (
            <EmptyState
              title="No receipts yet"
              message="Receipts are generated automatically when you end a paid parking session."
            />
          ) : (
            receipts.map((r) => (
              <article key={r.id} className="history-row surface">
                <div className="history-row-main">
                  <h3>Receipt #{r.id.split("-").pop().toUpperCase()}</h3>
                  <p className="history-row-sub">
                    {r.zoneName} · Space {r.spaceNumber || "—"} · {r.plateNumber || "—"}
                  </p>
                  <p className="history-row-sub">
                    {formatClockTime(r.startedAt)} – {formatClockTime(r.endedAt)} on{" "}
                    {formatShortDate(r.endedAt)}
                  </p>
                </div>
                <div className="history-row-amount">{Number(r.amount).toFixed(2)} EGP</div>
              </article>
            ))
          )}
        </div>
      )}

      {activeTab === "violations" && (
        <div className="history-list">
          {violations.length === 0 ? (
            <EmptyState
              title="No violations on record"
              message="AI-assisted violations (overstay, restricted-zone parking, improper parking) will appear here once flagged and reviewed."
            />
          ) : (
            violations.map((v) => (
              <article key={v.id} className="history-row surface">
                <div className="history-row-main">
                  <h3>{v.type}</h3>
                  <p className="history-row-sub">
                    {v.zoneName} · {formatShortDate(v.createdAt)}
                  </p>
                </div>
                <StatusPill status={v.status} />
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
}
