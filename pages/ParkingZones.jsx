import { useEffect, useState } from "react";
import ParkingCard from "../components/ParkingCard";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import { getParkingZones } from "../services/api";
import "./ParkingZones.css";

export default function ParkingZones() {
  const [zones, setZones] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    let isMounted = true;

    async function loadZones() {
      setStatus("loading");
      try {
        const data = await getParkingZones();
        if (isMounted) {
          setZones(data);
          setStatus("ready");
        }
      } catch {
        if (isMounted) setStatus("error");
      }
    }

    loadZones();
    return () => {
      isMounted = false;
    };
  }, []);

  const totalAvailable = zones.reduce((sum, zone) => sum + zone.available, 0);

  return (
    <div className="page-container">
      <div className="page-header">
        <span className="eyebrow">Driver Portal</span>
        <h1>Parking Zones</h1>
        <p>
          Live occupancy across Aswan, tracked by the AI detection service and updated as spaces
          open up.
        </p>
      </div>

      {status === "ready" && zones.length > 0 && (
        <p className="zones-summary">
          <strong>{totalAvailable}</strong> spaces available right now across {zones.length} zones.
        </p>
      )}

      {status === "loading" && <Loading label="Fetching zone availability…" />}

      {status === "error" && (
        <EmptyState
          title="Couldn't load parking zones"
          message="Something went wrong while checking availability. Please try again."
          actionLabel="Retry"
          onAction={() => window.location.reload()}
        />
      )}

      {status === "ready" && zones.length === 0 && (
        <EmptyState
          title="No parking zones yet"
          message="Zones will appear here as soon as they're added to the system."
        />
      )}

      {status === "ready" && zones.length > 0 && (
        <div className="zones-grid">
          {zones.map((zone) => (
            <ParkingCard key={zone.id} zone={zone} />
          ))}
        </div>
      )}
    </div>
  );
}
