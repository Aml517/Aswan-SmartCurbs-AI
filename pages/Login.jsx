import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
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

    // Fake authentication — no backend call. The Backend team will replace
    // this with a real POST /api/auth/login once it's ready.
    setTimeout(() => {
      localStorage.setItem("driverEmail", email.trim());
      setIsSubmitting(false);
      navigate("/parking-zones");
    }, 500);
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
            <h1>Welcome back</h1>
            <p>Sign in to find and reserve a parking spot.</p>
          </div>

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              placeholder="driver@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
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
            {isSubmitting ? "Signing in…" : "Log in"}
          </button>

          <p className="login-card-footnote">
            Demo mode — any email and password will sign you in.
          </p>
        </form>
      </div>
    </div>
  );
}
