import { useEffect, useState } from "react";

// --------------------------------------------------------------------------
// Requests the driver's current position once (on first use) so parking
// pages can show a "1.4 km away" style distance, per the User Portal
// roadmap's "Distance/location" requirement (section 4.2 / 4.4).
//
// Reuses the browser's own geolocation + the zone's existing lat/lng — no
// new mapping infrastructure, consistent with "Existing mapping
// infrastructure should be reused rather than rebuilding navigation."
// --------------------------------------------------------------------------

export default function useUserLocation() {
  const [location, setLocation] = useState(null); // { lat, lng } | null
  const [status, setStatus] = useState("idle"); // idle | loading | ready | denied | unsupported | error

  useEffect(() => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setStatus("unsupported");
      return;
    }

    setStatus("loading");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({ lat: position.coords.latitude, lng: position.coords.longitude });
        setStatus("ready");
      },
      (error) => {
        setStatus(error?.code === error?.PERMISSION_DENIED ? "denied" : "error");
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 120000 }
    );
  }, []);

  return { location, status };
}
