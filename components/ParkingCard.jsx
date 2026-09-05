import { useNavigate } from "react-router-dom";
import "./ParkingCard.css";

function getStatus(occupancyPercent) {
  if (occupancyPercent >= 95) return { key: "full", label: "Full" };
  if (occupancyPercent >= 70) return { key: "limited", label: "Filling up" };
  return { key: "open", label: "Open" };
}

export default function ParkingCard({ zone }) {
  const navigate = useNavigate();
  const occupancyPercent = Math.round((zone.occupied / zone.capacity) * 100);
  const status = getStatus(occupancyPercent);

  return (
    <article className="parking-card surface">
      <div className={`parking-card-strip parking-card-strip-${status.key}`} aria-hidden="true" />
      <div className="parking-card-body">
        <div className="parking-card-top">
          <h3>{zone.name}</h3>
          <span className={`pill pill-${status.key}`}>{status.label}</span>
        </div>

        <p className="parking-card-address">{zone.address}</p>

        <dl className="parking-card-stats">
          <div>
            <dt>Capacity</dt>
            <dd>{zone.capacity}</dd>
          </div>
          <div>
            <dt>Available</dt>
            <dd className="stat-available">{zone.available}</dd>
          </div>
          <div>
            <dt>Occupied</dt>
            <dd>{zone.occupied}</dd>
          </div>
        </dl>

        <div className="parking-card-bar" role="img" aria-label={`${occupancyPercent}% occupied`}>
          <div
            className={`parking-card-bar-fill parking-card-bar-fill-${status.key}`}
            style={{ width: `${occupancyPercent}%` }}
          />
        </div>

        <button type="button" className="btn btn-secondary btn-block" onClick={() => navigate(`/parking-zones/${zone.id}`)}>
          View Details
        </button>
      </div>
    </article>
  );
}
