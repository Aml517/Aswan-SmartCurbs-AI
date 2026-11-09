import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ParkingZones from "./pages/ParkingZones";
import ParkingDetails from "./pages/ParkingDetails";
import Reservation from "./pages/Reservation";
import ParkingSession from "./pages/ParkingSession";
import History from "./pages/History";

export default function App() {
  const location = useLocation();

  // إخفاء الـ Navbar تماماً في صفحة التسجيل وصفحة الدخول
  const hideNavbar = location.pathname === "/login" || location.pathname === "/register";

  return (
    <div className="page">
      {/* لن يظهر إلا بعد تسجيل الدخول وفي الصفحات الداخلية فقط */}
      {!hideNavbar && <Navbar />}

      <Routes>
        {/* Login is the default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

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
        <Route
          path="/session/:sessionId"
          element={
            <ProtectedRoute>
              <ParkingSession />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />

        {/* Unknown paths fall back to Login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </div>
  );
}