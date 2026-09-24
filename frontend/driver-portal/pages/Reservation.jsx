import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { getParkingZoneById, getParkingAvailability, createReservation } from "../services/api";
import "./Reservation.css";

function getInitialDateTime() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const defaultDate = `${year}-${month}-${day}`;

  const hours = now.getHours();
  const mins = now.getMinutes();
  const roundedMins = Math.ceil(mins / 15) * 15;
  const startObj = new Date(year, now.getMonth(), now.getDate(), hours, roundedMins);
  const startH = String(startObj.getHours()).padStart(2, "0");
  const startM = String(startObj.getMinutes()).padStart(2, "0");
  const defaultStart = `${startH}:${startM}`;

  const endObj = new Date(startObj.getTime() + 90 * 60000); // +90 mins
  const endH = String(endObj.getHours()).padStart(2, "0");
  const endM = String(endObj.getMinutes()).padStart(2, "0");
  const defaultEnd = `${endH}:${endM}`;

  return { defaultDate, defaultStart, defaultEnd };
}

function formatReservationDateTime(startIso, endIso) {
  if (!startIso) return { dateStr: "Today", dayStr: "", timeWindow: "Now", durationStr: "1.5 hrs" };

  const startMatch = String(startIso).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
  let startDateObj = new Date(startIso);
  let year, month, day, startHours, startMins;

  if (startMatch) {
    year = parseInt(startMatch[1], 10);
    month = parseInt(startMatch[2], 10) - 1;
    day = parseInt(startMatch[3], 10);
    startHours = parseInt(startMatch[4], 10);
    startMins = parseInt(startMatch[5], 10);
    startDateObj = new Date(year, month, day, startHours, startMins);
  } else {
    year = startDateObj.getFullYear();
    month = startDateObj.getMonth();
    day = startDateObj.getDate();
    startHours = startDateObj.getHours();
    startMins = startDateObj.getMinutes();
  }

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  const dateStr = `${day} ${months[month]} ${year}`;
  const dayStr = days[startDateObj.getDay()];

  const formatTime12 = (h, m) => {
    const ampm = h >= 12 ? "PM" : "AM";
    const h12 = h % 12 === 0 ? 12 : h % 12;
    const mStr = String(m).padStart(2, "0");
    return `${h12}:${mStr} ${ampm}`;
  };

  const startTimeFormatted = formatTime12(startHours, startMins);
  let endTimeFormatted = "";
  let durationStr = "1.5 hrs";

  if (endIso) {
    const endMatch = String(endIso).match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/);
    let endHours, endMins, endDateObj;
    if (endMatch) {
      endHours = parseInt(endMatch[4], 10);
      endMins = parseInt(endMatch[5], 10);
      endDateObj = new Date(
        parseInt(endMatch[1], 10),
        parseInt(endMatch[2], 10) - 1,
        parseInt(endMatch[3], 10),
        endHours,
        endMins
      );
    } else {
      endDateObj = new Date(endIso);
      endHours = endDateObj.getHours();
      endMins = endDateObj.getMinutes();
    }
    endTimeFormatted = formatTime12(endHours, endMins);

    const diffMs = endDateObj.getTime() - startDateObj.getTime();
    const diffMins = Math.round(diffMs / 60000);
    if (diffMins > 0) {
      if (diffMins % 60 === 0) {
        durationStr = `${diffMins / 60} ${diffMins === 60 ? "hr" : "hrs"}`;
      } else {
        const hours = (diffMins / 60).toFixed(1).replace(/\.0$/, "");
        durationStr = `${hours} hrs`;
      }
    }
  }

  const timeWindow = endTimeFormatted ? `${startTimeFormatted} - ${endTimeFormatted}` : startTimeFormatted;

  return {
    dateStr,
    dayStr,
    startTimeFormatted,
    endTimeFormatted,
    timeWindow,
    durationStr,
  };
}

export default function Reservation() {
  const [searchParams] = useSearchParams();
  const zoneId = searchParams.get("zoneId");
  const spaceId = searchParams.get("spaceId");
  const navigate = useNavigate();

  const [zone, setZone] = useState(null);
  const [space, setSpace] = useState(null);
  const [loadStatus, setLoadStatus] = useState("loading"); // loading | ready | error

  const initialDt = getInitialDateTime();
  const [reservationDate, setReservationDate] = useState(initialDt.defaultDate);
  const [startTime, setStartTime] = useState(initialDt.defaultStart);
  const [endTime, setEndTime] = useState(initialDt.defaultEnd);

  const [driverName, setDriverName] = useState(() => localStorage.getItem("driverName") || "");
  const [driverEmail, setDriverEmail] = useState(() => localStorage.getItem("driverEmail") || "");
  const [driverPhone, setDriverPhone] = useState(() => localStorage.getItem("driverPhone") || "");
  const [plateNumber, setPlateNumber] = useState(() => localStorage.getItem("vehiclePlate") || "");
  const [vehicleModel, setVehicleModel] = useState(() => localStorage.getItem("vehicleModel") || "Car — Sedan");

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
    const trimmedEmail = driverEmail.trim();
    const trimmedPhone = driverPhone.trim();
    const trimmedPlate = plateNumber.trim();
    const trimmedModel = vehicleModel.trim() || "Car — Sedan";

    if (!trimmedName) {
      setFormError("Enter your full name to reserve this space.");
      return;
    }
    if (!trimmedPlate) {
      setFormError("Enter your vehicle's plate number to reserve this space.");
      return;
    }
    if (!reservationDate || !startTime) {
      setFormError("Please select a reservation date and start time.");
      return;
    }

    setIsSubmitting(true);
    try {
      localStorage.setItem("driverName", trimmedName);
      if (trimmedEmail) localStorage.setItem("driverEmail", trimmedEmail);
      if (trimmedPhone) localStorage.setItem("driverPhone", trimmedPhone);
      localStorage.setItem("vehiclePlate", trimmedPlate);
      localStorage.setItem("vehicleModel", trimmedModel);

      const startIso = `${reservationDate}T${startTime}:00`;
      const endIso = endTime ? `${reservationDate}T${endTime}:00` : null;

      const result = await createReservation({
        spaceId,
        driverName: trimmedName,
        driverEmail: trimmedEmail,
        driverPhone: trimmedPhone,
        plateNumber: trimmedPlate,
        vehicleModel: trimmedModel,
        startTime: startIso,
        endTime: endIso,
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
    const dtInfo = formatReservationDateTime(reservation.startTime, reservation.endTime);

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
          <dl className="reservation-receipt-grid">
            <div>
              <dt>Reservation ID</dt>
              <dd>#{reservation.id}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd className="reservation-receipt-status">{reservation.status}</dd>
            </div>
            <div>
              <dt>Driver Name</dt>
              <dd><strong>{reservation.driverName}</strong></dd>
            </div>
            <div>
              <dt>Vehicle</dt>
              <dd>{reservation.vehicleModel || "Car"} — <strong>{reservation.plateNumber}</strong></dd>
            </div>
            {reservation.driverEmail && (
              <div>
                <dt>Email</dt>
                <dd>{reservation.driverEmail}</dd>
              </div>
            )}
            {reservation.driverPhone && (
              <div>
                <dt>Phone</dt>
                <dd>{reservation.driverPhone}</dd>
              </div>
            )}
            <div>
              <dt>Date</dt>
              <dd>{dtInfo.dateStr} <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>({dtInfo.dayStr})</span></dd>
            </div>
            <div>
              <dt>Time Window</dt>
              <dd>{dtInfo.timeWindow} <span style={{ color: "var(--text-secondary)", fontWeight: 400 }}>({dtInfo.durationStr})</span></dd>
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

  const previewDt = formatReservationDateTime(
    `${reservationDate}T${startTime}:00`,
    endTime ? `${reservationDate}T${endTime}:00` : null
  );

  const isFreeZone = zone.type === "FREE";
  const rateLabel = isFreeZone
    ? "Free (0 EGP)"
    : zone.hourlyRate !== null && zone.hourlyRate !== undefined
    ? `${zone.hourlyRate} EGP / hr`
    : "Standard Rate";

  return (
    <div className="page-container">
      <Link to={`/parking-zones/${zone.id}`} className="details-back">
        ← Back to {zone.name}
      </Link>

      <div className="reservation-layout">
        <form className="reservation-form surface" onSubmit={handleSubmit} noValidate>
          <div className="page-header" style={{ marginBottom: "var(--space-5)" }}>
            <span className="eyebrow">{isFreeZone ? "Free Municipal Parking" : "Reserve Parking"}</span>
            <h1>Space {space.number}</h1>
            <p>
              {isFreeZone
                ? `Confirm your arrival details to hold this free spot in ${zone.name}. No payment required.`
                : `Confirm your schedule, profile, and vehicle details to hold this space in ${zone.name}.`}
            </p>
          </div>

          <div className="field">
            <label htmlFor="reservationDate">Reservation Date</label>
            <input
              id="reservationDate"
              type="date"
              value={reservationDate}
              onChange={(event) => setReservationDate(event.target.value)}
              required
            />
          </div>

          <div className="fields-row">
            <div className="field">
              <label htmlFor="startTime">Start Time</label>
              <input
                id="startTime"
                type="time"
                value={startTime}
                onChange={(event) => setStartTime(event.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="endTime">End Time</label>
              <input
                id="endTime"
                type="time"
                value={endTime}
                onChange={(event) => setEndTime(event.target.value)}
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="driverName">Full Name</label>
            <input
              id="driverName"
              type="text"
              placeholder="e.g. Test Integration User"
              value={driverName}
              onChange={(event) => setDriverName(event.target.value)}
              autoComplete="name"
            />
          </div>

          <div className="field">
            <label htmlFor="driverEmail">Email Address</label>
            <input
              id="driverEmail"
              type="email"
              placeholder="e.g. integrationtest@example.com"
              value={driverEmail}
              onChange={(event) => setDriverEmail(event.target.value)}
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label htmlFor="driverPhone">Phone Number</label>
            <input
              id="driverPhone"
              type="tel"
              placeholder="e.g. +20 100 000 0001"
              value={driverPhone}
              onChange={(event) => setDriverPhone(event.target.value)}
              autoComplete="tel"
            />
          </div>

          <div className="field">
            <label htmlFor="plateNumber">Vehicle Plate Number</label>
            <input
              id="plateNumber"
              type="text"
              placeholder="e.g. TEST 999"
              value={plateNumber}
              onChange={(event) => setPlateNumber(event.target.value)}
              autoComplete="off"
            />
            <span className="field-hint">Match the plate exactly as shown on your vehicle.</span>
          </div>

          <div className="field">
            <label htmlFor="vehicleModel">Vehicle Type / Model</label>
            <input
              id="vehicleModel"
              type="text"
              placeholder="e.g. Car — Sedan"
              value={vehicleModel}
              onChange={(event) => setVehicleModel(event.target.value)}
            />
          </div>

          {formError && (
            <p className="field-error" role="alert">
              {formError}
            </p>
          )}

          <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
            {isSubmitting
              ? "Reserving…"
              : isFreeZone
              ? "Reserve Free Spot"
              : "Reserve Spot"}
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
              <dt>Zone Policy</dt>
              <dd>{zone.type || "PAID"}</dd>
            </div>
            <div>
              <dt>Tariff</dt>
              <dd>{rateLabel}</dd>
            </div>
            <div>
              <dt>Space</dt>
              <dd>{space.number}</dd>
            </div>
            <div>
              <dt>Date</dt>
              <dd>{previewDt.dateStr}</dd>
            </div>
            <div>
              <dt>Time</dt>
              <dd>{previewDt.timeWindow}</dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{previewDt.durationStr}</dd>
            </div>
            <div>
              <dt>Driver</dt>
              <dd>{driverName || "Driver"}</dd>
            </div>
            <div>
              <dt>Vehicle</dt>
              <dd>{plateNumber ? `${vehicleModel ? vehicleModel + " — " : ""}${plateNumber}` : "Not entered"}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </div>
  );
}

