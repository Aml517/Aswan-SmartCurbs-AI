import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const isLoginPage = location.pathname === "/" || location.pathname === "/login";
  const driverName = localStorage.getItem("driverEmail");

  function handleLogout() {
    localStorage.removeItem("driverEmail");
    navigate("/");
  }

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to={isLoginPage ? "/login" : "/parking-zones"} className="navbar-brand">
          <span className="navbar-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" width="22" height="22">
              <path
                d="M4 22 L16 6 L28 22"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="16" cy="24" r="2.4" fill="currentColor" />
            </svg>
          </span>
          <span className="navbar-brand-text">
            Aswan SmartCurbs <em>AI</em>
          </span>
        </Link>

        {!isLoginPage && (
          <nav className="navbar-links">
            <Link to="/parking-zones">Parking Zones</Link>
            {driverName && <span className="navbar-driver">{driverName}</span>}
            <button type="button" className="navbar-logout" onClick={handleLogout}>
              Log out
            </button>
          </nav>
        )}
      </div>
    </header>
  );
}
