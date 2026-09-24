import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { getParkingZoneById, getParkingAvailability } from "../services/api";
import "./ParkingDetails.css";

function getZoneStatus(type, available, occupied, capacity) {
  if (type === "RESTRICTED") {
    return { key: "restricted", label: "Restricted" };
  }
  if (available === 0 || (capacity > 0 && occupied >= capacity)) {
    return { key: "full", label: "Full" };
  }
  const occupancyPercent = capacity > 0 ? Math.round((occupied / capacity) * 100) : 0;
  if (occupancyPercent >= 70) {
    return { key: "limited", label: "Filling up" };
  }
  return { key: "open", label: "Available" };
}

function getZoneTypePill(type) {
  const t = (type || "PAID").toUpperCase();
  if (t === "FREE") return { key: "free", label: "FREE" };
  if (t === "RESTRICTED") return { key: "restricted", label: "RESTRICTED" };
  return { key: "paid", label: "PAID" };
}

function formatPrice(type, hourlyRate) {
  if (type === "FREE") return "Free (0 EGP)";
  if (type === "RESTRICTED") return "No public parking";
  if (hourlyRate !== null && hourlyRate !== undefined) return `${hourlyRate} EGP / hour`;
  return "Standard municipal rate";
}

export default function ParkingDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [zone, setZone] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [selectedSpaceId, setSelectedSpaceId] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadDetails() {
      setStatus("loading");
      try {
        const [zoneData, availabilityData] = await Promise.all([
          getParkingZoneById(id),
          getParkingAvailability(id),
        ]);
        if (isMounted) {
          setZone(zoneData);
          setAvailability(availabilityData);
          const firstAvailable = availabilityData.spaces.find((s) => s.status === "available");
          setSelectedSpaceId(firstAvailable ? String(firstAvailable.id) : "");
          setStatus("ready");
        }
      } catch {
        if (isMounted) setStatus("error");
      }
    }

    loadDetails();
    return () => {
      isMounted = false;
    };
  }, [id]);

  const availableSpaces = useMemo(
    () => availability?.spaces.filter((s) => s.status === "available") || [],
    [availability]
  );

  if (status === "loading") {
    return (
      <div className="page-container">
        <Loading label="Loading zone details…" />
      </div>
    );
  }

  if (status === "error" || !zone) {
    return (
      <div className="page-container">
        <EmptyState
          title="Zone not found"
          message="This parking zone may have been removed, or the backend couldn't be reached."
          actionLabel="Back to zones"
          onAction={() => navigate("/parking-zones")}
        />
      </div>
    );
  }

  const zoneType = getZoneTypePill(zone.type);
  const isRestricted = zone.type === "RESTRICTED";
  const isFree = zone.type === "FREE";

  const zoneStatus = getZoneStatus(
    zone.type,
    availability.available,
    availability.occupied,
    zone.capacity
  );

  const hasAvailableSpaces = !isRestricted && availableSpaces.length > 0;

  const occupancyDisplayPercent = isRestricted
    ? 100
    : availability.occupancyPercent;

  function handleReserve() {
    if (!selectedSpaceId || isRestricted) return;
    navigate(`/reservation?zoneId=${zone.id}&spaceId=${selectedSpaceId}`);
  }

  function handleDirections() {
    if (zone.latitude && zone.longitude) {
      window.open(`https://www.google.com/maps/search/?api=1&query=${zone.latitude},${zone.longitude}`, "_blank");
    } else {
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(zone.address || zone.name)}`, "_blank");
    }
  }

  return (
    <div className="page-container">
      <Link to="/parking-zones" className="details-back">
        ← All zones
      </Link>

      <div className="details-layout">
        <div className="details-main surface">
          <div className="details-main-header">
            <div>
              <div className="details-badges">
                <span className={`pill pill-type-${zoneType.key}`}>[ {zoneType.label} ]</span>
                <span className={`pill pill-${zoneStatus.key}`}>{zoneStatus.label}</span>
              </div>
              <h1>{zone.name}</h1>
              <p className="details-address">{zone.address}</p>
            </div>
            <div className="details-percent">
              <span className="details-percent-value">
                {isRestricted ? "N/A" : `${availability.occupancyPercent}%`}
              </span>
              <span className="details-percent-label">
                {isRestricted ? "Restricted" : "Occupied"}
              </span>
            </div>
          </div>

          <div
            className="details-bar"
            role="img"
            aria-label={isRestricted ? "Parking Restricted" : `${availability.occupancyPercent}% occupied`}
          >
            <div
              className={`details-bar-fill details-bar-fill-${zoneStatus.key}`}
              style={{ width: `${occupancyDisplayPercent}%` }}
            />
          </div>

          <dl className="details-stats">
            <div>
              <dt>Capacity</dt>
              <dd>{zone.capacity}</dd>
            </div>
            <div>
              <dt>Available</dt>
              <dd className={isRestricted ? "stat-restricted" : "stat-available"}>
                {isRestricted ? "0" : availability.available}
              </dd>
            </div>
            <div>
              <dt>{isRestricted ? "Policy" : "Occupied"}</dt>
              <dd>{isRestricted ? "Restricted" : availability.occupied}</dd>
            </div>
            <div>
              <dt>Reserved</dt>
              <dd>{isRestricted ? "0" : availability.reserved}</dd>
            </div>
          </dl>

          {/* Parking Information Section */}
          <div className="details-info-section">
            <h3>Parking Information & Policy</h3>
            <div className="details-info-grid">
              <div className="details-info-item">
                <dt>Zone Classification</dt>
                <dd>{zoneType.label} Parking</dd>
              </div>
              <div className="details-info-item">
                <dt>Tariff / Price</dt>
                <dd>{formatPrice(zone.type, zone.hourlyRate)}</dd>
              </div>
              <div className="details-info-item">
                <dt>Operating Hours</dt>
                <dd>{zone.operatingHours || "24 Hours / 7 Days"}</dd>
              </div>
              <div className="details-info-item">
                <dt>Parking Rules</dt>
                <dd>{zone.rules || "Standard municipal curb parking regulations"}</dd>
              </div>
            </div>
          </div>
        </div>

        <aside className="details-side surface">
          {isRestricted ? (
            <div>
              <h2>Parking Restricted</h2>
              <div className="restriction-callout">
                <div className="restriction-callout-header">
                  <span aria-hidden="true">⚠️</span>
                  <span>Why can't I park here?</span>
                </div>
                <p>This zone is currently designated as restricted by local municipal policy.</p>
                <div className="restriction-callout-reason">
                  Reason: {zone.restrictionReason || "Parking is currently restricted in this zone."}
                </div>
              </div>

              <div className="details-action-group">
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  disabled
                  style={{ background: "var(--color-granite-500)", cursor: "not-allowed" }}
                >
                  Parking Not Available
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  onClick={() => navigate("/parking-zones")}
                >
                  Browse Other Zones
                </button>
              </div>
            </div>
          ) : isFree ? (
            <div>
              <h2>Free Public Parking</h2>
              <p>
                This zone provides free public curb parking. No reservation fee or payment is
                required.
              </p>

              <div
                className="restriction-callout"
                style={{
                  background: "var(--color-success-100)",
                  borderColor: "rgba(41, 118, 79, 0.25)",
                }}
              >
                <div
                  className="restriction-callout-header"
                  style={{ color: "var(--color-success-600)" }}
                >
                  <span aria-hidden="true">✓</span>
                  <span>Free Municipal Curb</span>
                </div>
                <p style={{ color: "var(--color-granite-800)", marginBottom: 0 }}>
                  {hasAvailableSpaces
                    ? `${availability.available} of ${zone.capacity} spaces are currently open for public parking.`
                    : "All free parking spaces in this zone are currently occupied."}
                </p>
              </div>

              <div className="details-action-group">
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={handleDirections}
                >
                  Get Directions ↗
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  onClick={() => navigate("/parking-zones")}
                >
                  Browse Other Zones
                </button>
              </div>
            </div>
          ) : (
            <div>
              <h2>Reserve this zone</h2>
              {hasAvailableSpaces ? (
                <>
                  <p>
                    Pick a free space, then confirm your vehicle details on the next step.
                    Rate: <strong>{formatPrice(zone.type, zone.hourlyRate)}</strong>.
                  </p>
                  <div className="field">
                    <label htmlFor="spaceSelect">Available space</label>
                    <select
                      id="spaceSelect"
                      value={selectedSpaceId}
                      onChange={(event) => setSelectedSpaceId(event.target.value)}
                    >
                      {availableSpaces.map((space) => (
                        <option key={space.id} value={space.id}>
                          Space {space.number}
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              ) : (
                <p style={{ color: "var(--color-danger-600)", fontWeight: 600 }}>
                  There are no free spaces in this zone right now.
                </p>
              )}

              <div className="details-action-group">
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  disabled={!hasAvailableSpaces}
                  onClick={handleReserve}
                >
                  {hasAvailableSpaces ? "Reserve Parking" : "Zone Full"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  onClick={handleDirections}
                >
                  Get Directions ↗
                </button>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
