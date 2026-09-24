import { useNavigate } from "react-router-dom";
import "./ParkingCard.css";

function getZoneStatus(zone) {
  if (zone.type === "RESTRICTED") {
    return { key: "restricted", label: "Restricted" };
  }
  if (zone.available === 0 || (zone.capacity > 0 && zone.occupied >= zone.capacity)) {
    return { key: "full", label: "Full" };
  }
  const occupancyPercent = zone.capacity > 0 ? Math.round((zone.occupied / zone.capacity) * 100) : 0;
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

export default function ParkingCard({ zone }) {
  const navigate = useNavigate();
  const zoneType = getZoneTypePill(zone.type);
  const status = getZoneStatus(zone);
  const isRestricted = zone.type === "RESTRICTED";

  const occupancyPercent = isRestricted
    ? 100
    : zone.capacity > 0
    ? Math.min(100, Math.round((zone.occupied / zone.capacity) * 100))
    : 0;

  return (
    <article className="parking-card surface">
      <div className={`parking-card-strip parking-card-strip-${status.key}`} aria-hidden="true" />
      <div className="parking-card-body">
        <div className="parking-card-top">
          <div>
            <h3>{zone.name}</h3>
            <p className="parking-card-address">{zone.address}</p>
          </div>
          <div className="parking-card-badges">
            <span className={`pill pill-type-${zoneType.key}`}>[ {zoneType.label} ]</span>
            <span className={`pill pill-${status.key}`}>{status.label}</span>
          </div>
        </div>

        <dl className="parking-card-stats">
          <div>
            <dt>Capacity</dt>
            <dd>{zone.capacity}</dd>
          </div>
          <div>
            <dt>Available</dt>
            <dd className={isRestricted ? "stat-restricted" : "stat-available"}>
              {isRestricted ? "0" : zone.available}
            </dd>
          </div>
          <div>
            <dt>{isRestricted ? "Policy" : "Occupied"}</dt>
            <dd>{isRestricted ? "Restricted" : zone.occupied}</dd>
          </div>
        </dl>

        <div
          className="parking-card-bar"
          role="img"
          aria-label={isRestricted ? "Parking Restricted" : `${occupancyPercent}% occupied`}
        >
          <div
            className={`parking-card-bar-fill parking-card-bar-fill-${status.key}`}
            style={{ width: `${occupancyPercent}%` }}
          />
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-block"
          onClick={() => navigate(`/parking-zones/${zone.id}`)}
        >
          View Details
        </button>
      </div>
    </article>
  );
}
