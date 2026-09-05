import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { getParkingZoneById, getParkingAvailability, createReservation } from "../services/api";
import "./Reservation.css";

export default function Reservation() {
  const [searchParams] = useSearchParams();
  const zoneId = searchParams.get("zoneId");
  const spaceId = searchParams.get("spaceId");
  const navigate = useNavigate();

  const [zone, setZone] = useState(null);
  const [space, setSpace] = useState(null);
  const [loadStatus, setLoadStatus] = useState("loading"); // loading | ready | error

  const [driverName, setDriverName] = useState("");
  const [plateNumber, setPlateNumber] = useState("");
  const [formError, setFormError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reservation, setReservation] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadContext() {
      if (!zoneId || !spaceId) {
        if (isMounted) setLoadStatus("error");
        return;
      }
      setLoadStatus("loading");
      try {
        const [zoneData, availabilityData] = await Promise.all([
          getParkingZoneById(zoneId),
          getParkingAvailability(zoneId),
        ]);
        const matchedSpace = availabilityData.spaces.find((s) => String(s.id) === String(spaceId));
        if (!isMounted) return;

        if (!matchedSpace || matchedSpace.status !== "available") {
          setLoadStatus("error");
          return;
        }
        setZone(zoneData);
        setSpace(matchedSpace);
        setLoadStatus("ready");
      } catch {
        if (isMounted) setLoadStatus("error");
      }
    }

    loadContext();
    return () => {
      isMounted = false;
    };
  }, [zoneId, spaceId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    const trimmedName = driverName.trim();
    const trimmedPlate = plateNumber.trim();

    if (!trimmedName) {
      setFormError("Enter your full name to reserve this space.");
      return;
    }
    if (!trimmedPlate) {
      setFormError("Enter your vehicle's plate number to reserve this space.");
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await createReservation({
        spaceId,
        driverName: trimmedName,
        plateNumber: trimmedPlate,
      });
      setReservation(result);
    } catch (err) {
      setFormError(err.message || "Reservation failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loadStatus === "loading") {
    return (
      <div className="page-container">
        <Loading label="Preparing reservation…" />
      </div>
    );
  }

  if (loadStatus === "error" || !zone || !space) {
    return (
      <div className="page-container">
        <EmptyState
          title="This space isn't available anymore"
          message="It may have just been taken, or the link is missing details. Head back and pick another space."
          actionLabel="Back to zones"
          onAction={() => navigate("/parking-zones")}
        />
      </div>
    );
  }

  if (reservation) {
    return (
      <div className="page-container">
        <div className="reservation-success surface">
          <div className="reservation-success-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" width="30" height="30">
              <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2" />
              <path
                d="M10 16.5 L14 20.5 L22 11.5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h1>Reservation Created Successfully</h1>
          <p>
            Space <strong>{space.number}</strong> in <strong>{zone.name}</strong> is held for plate{" "}
            <strong>{reservation.plateNumber}</strong>.
          </p>
          <dl className="reservation-receipt">
            <div>
              <dt>Reservation ID</dt>
              <dd>#{reservation.id}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd className="reservation-receipt-status">{reservation.status}</dd>
            </div>
          </dl>
          <div className="reservation-success-actions">
            <button type="button" className="btn btn-secondary" onClick={() => navigate(`/parking-zones/${zone.id}`)}>
              Back to Zone
            </button>
            <button type="button" className="btn btn-primary" onClick={() => navigate("/parking-zones")}>
              Browse Other Zones
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <Link to={`/parking-zones/${zone.id}`} className="details-back">
        ← Back to {zone.name}
      </Link>

      <div className="reservation-layout">
        <form className="reservation-form surface" onSubmit={handleSubmit} noValidate>
          <div className="page-header" style={{ marginBottom: "var(--space-5)" }}>
            <span className="eyebrow">Reserve Parking</span>
            <h1>Space {space.number}</h1>
            <p>Confirm your details to hold this space in {zone.name}.</p>
          </div>

          <div className="field">
            <label htmlFor="driverName">Full Name</label>
            <input
              id="driverName"
              type="text"
              placeholder="e.g. Ahmed Mohamed"
              value={driverName}
              onChange={(event) => setDriverName(event.target.value)}
              autoComplete="name"
            />
          </div>

          <div className="field">
            <label htmlFor="plateNumber">Vehicle Plate Number</label>
            <input
              id="plateNumber"
              type="text"
              placeholder="e.g. ASW 1234"
              value={plateNumber}
              onChange={(event) => setPlateNumber(event.target.value)}
              autoComplete="off"
            />
            <span className="field-hint">Match the plate exactly as shown on your vehicle.</span>
          </div>

          {formError && (
            <p className="field-error" role="alert">
              {formError}
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
            {isSubmitting ? "Reserving…" : "Reserve Spot"}
          </button>
        </form>

        <aside className="reservation-summary surface">
          <h2>Summary</h2>
          <dl>
            <div>
              <dt>Zone</dt>
              <dd>{zone.name}</dd>
            </div>
            <div>
              <dt>Space</dt>
              <dd>{space.number}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>{zone.address}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </div>
  );
}
