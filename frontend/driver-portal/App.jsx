import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import ParkingZones from "./pages/ParkingZones";
import ParkingDetails from "./pages/ParkingDetails";
import Reservation from "./pages/Reservation";

export default function App() {
  return (
    <div className="page">
      <Navbar />
      <Routes>
        {/* Login is the default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />

        <Route
          path="/parking-zones"
          element={
            <ProtectedRoute>
              <ParkingZones />
            </ProtectedRoute>
          }
        />
        <Route
          path="/parking-zones/:id"
          element={
            <ProtectedRoute>
              <ParkingDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reservation"
          element={
            <ProtectedRoute>
              <Reservation />
            </ProtectedRoute>
          }
        />

        {/* Unknown paths fall back to Login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}
