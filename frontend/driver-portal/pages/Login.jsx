import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [name, setName] = useState(() => localStorage.getItem("driverName") || "");
  const [email, setEmail] = useState(() => localStorage.getItem("driverEmail") || "");
  const [phone, setPhone] = useState(() => localStorage.getItem("driverPhone") || "");
  const [plate, setPlate] = useState(() => localStorage.getItem("vehiclePlate") || "");
  const [vehicleModel, setVehicleModel] = useState(() => localStorage.getItem("vehicleModel") || "Car — Sedan");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Enter both an email and a password to continue.");
      return;
    }

    setIsSubmitting(true);

    setTimeout(() => {
      const derivedName = name.trim() || email.split("@")[0].replace(".", " ").replace(/\b\w/g, (c) => c.toUpperCase());
      localStorage.setItem("driverName", derivedName);
      localStorage.setItem("driverEmail", email.trim());
      localStorage.setItem("driverPhone", phone.trim() || "+20 100 000 0000");
      localStorage.setItem("vehiclePlate", plate.trim() || "ASW 1234");
      localStorage.setItem("vehicleModel", vehicleModel.trim() || "Car — Sedan");

      setIsSubmitting(false);
      navigate("/parking-zones");
    }, 300);
  }

  return (
    <div className="login-page">
      <div className="login-visual" aria-hidden="true">
        <div className="login-visual-inner">
          <span className="login-visual-eyebrow">Aswan SmartCurbs AI</span>
          <h2>Every open spot in the city, spotted in real time.</h2>
          <p>
            Vehicle-detection cameras track occupancy across Aswan's curbside zones so you can
            check availability and reserve a spot before you arrive.
          </p>
          <ul className="login-visual-stats">
            <li>
              <strong>3</strong>
              <span>zones live</span>
            </li>
            <li>
              <strong>120</strong>
              <span>tracked spaces</span>
            </li>
            <li>
              <strong>~2s</strong>
              <span>detection refresh</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="login-form-panel">
        <form className="login-card surface" onSubmit={handleSubmit} noValidate>
          <div className="login-card-header">
            <h1>Driver Portal Sign In</h1>
            <p>Enter your profile and vehicle details to sign in and reserve parking.</p>
          </div>

          <div className="field">
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              placeholder="e.g. Test User One"
              value={name}
              onChange={(event) => setName(event.target.value)}
              autoComplete="name"
            />
          </div>

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="e.g. test1@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label htmlFor="phone">Phone Number</label>
            <input
              id="phone"
              type="tel"
              placeholder="e.g. +20 111 111 1111"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              autoComplete="tel"
            />
          </div>

          <div className="field">
            <label htmlFor="plate">Vehicle License Plate</label>
            <input
              id="plate"
              type="text"
              placeholder="e.g. AAA 111"
              value={plate}
              onChange={(event) => setPlate(event.target.value)}
              autoComplete="off"
            />
          </div>

          <div className="field">
            <label htmlFor="vehicleModel">Vehicle Type / Model</label>
            <input
              id="vehicleModel"
              type="text"
              placeholder="e.g. Car — Sedan"
              value={vehicleModel}
              onChange={(event) => setVehicleModel(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </div>

          {error && <p className="field-error" role="alert">{error}</p>}

          <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
            {isSubmitting ? "Signing in…" : "Sign in & Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

