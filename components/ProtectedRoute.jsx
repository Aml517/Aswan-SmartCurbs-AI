import { Navigate, useLocation } from "react-router-dom";

/**
 * Wrap any route element that requires a signed-in driver.
 * Auth state is fake for this milestone — a "driverEmail" key in
 * localStorage, written by Login.jsx after the (mock) sign-in succeeds.
 * Unauthenticated visitors are bounced to /login, and we keep the
 * originally requested location so Login could send them back afterwards.
 */
export default function ProtectedRoute({ children }) {
  const location = useLocation();
  const isAuthenticated = Boolean(localStorage.getItem("driverEmail"));

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
