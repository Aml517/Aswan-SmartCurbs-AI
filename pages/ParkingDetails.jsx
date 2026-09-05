import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { getParkingZoneById, getParkingAvailability } from "../services/api";
import "./ParkingDetails.css";

function getStatus(occupancyPercent) {
  if (occupancyPercent >= 95) return { key: "full", label: "Full" };
  if (occupancyPercent >= 70) return { key: "limited", label: "Filling up" };
  return { key: "open", label: "Open" };
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

  const zoneStatus = getStatus(availability.occupancyPercent);
  const hasAvailableSpaces = availableSpaces.length > 0;

  function handleReserve() {
    if (!selectedSpaceId) return;
    navigate(`/reservation?zoneId=${zone.id}&spaceId=${selectedSpaceId}`);
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
              <span className={`pill pill-${zoneStatus.key}`}>{zoneStatus.label}</span>
              <h1>{zone.name}</h1>
              <p className="details-address">{zone.address}</p>
            </div>
            <div className="details-percent">
              <span className="details-percent-value">{availability.occupancyPercent}%</span>
              <span className="details-percent-label">Occupied</span>
            </div>
          </div>

          <div className="details-bar" role="img" aria-label={`${availability.occupancyPercent}% occupied`}>
            <div
              className={`details-bar-fill details-bar-fill-${zoneStatus.key}`}
              style={{ width: `${availability.occupancyPercent}%` }}
            />
          </div>

          <dl className="details-stats">
            <div>
              <dt>Capacity</dt>
              <dd>{zone.capacity}</dd>
            </div>
            <div>
              <dt>Available</dt>
              <dd className="stat-available">{availability.available}</dd>
            </div>
            <div>
              <dt>Occupied</dt>
              <dd>{availability.occupied}</dd>
            </div>
            <div>
              <dt>Reserved</dt>
              <dd>{availability.reserved}</dd>
            </div>
          </dl>
        </div>

        <aside className="details-side surface">
          <h2>Reserve this zone</h2>

          {hasAvailableSpaces ? (
            <>
              <p>Pick a free space, then confirm your vehicle's plate number on the next step.</p>
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
            <p>There are no free spaces in this zone right now.</p>
          )}

          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled={!hasAvailableSpaces}
            onClick={handleReserve}
          >
            {hasAvailableSpaces ? "Reserve Parking" : "No Spots Available"}
          </button>
        </aside>
      </div>
    </div>
  );
}
