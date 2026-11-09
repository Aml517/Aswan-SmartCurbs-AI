import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./Register.css"; // استخدام نفس الديزاين العصري الموحد

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState(() => localStorage.getItem("driverEmail") || "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      return;
    }

    setIsSubmitting(true);

    setTimeout(() => {
      // حفظ الجلسة والانتقال للمواقف
      localStorage.setItem("driverEmail", email.trim());
      setIsSubmitting(false);
      navigate("/parking-zones");
    }, 400);
  }

  return (
    <div className="modern-reg-wrapper">
      <div className="modern-reg-card">
        {/* الجانب الأيسر: رسمة العربية واللوجو بنفس ألوان المشروع */}
        <div className="reg-visual-side">
          <div className="reg-visual-header">
            <h2>Aswan SmartCurbs</h2>
            <p>Smart Curbside Parking & AI Occupancy</p>
          </div>

          <div className="car-scene">
            <svg className="car-svg" viewBox="0 0 500 220" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="250" cy="110" r="120" fill="#14b8a6" fillOpacity="0.15" filter="blur(20px)" />
              <path d="M70 140C90 140 105 110 140 100C190 85 280 85 340 105C380 115 410 125 440 135C455 140 460 155 450 165C430 175 100 175 70 165C55 160 55 140 70 140Z" fill="#14b8a6"/>
              <path d="M145 105L195 65C215 50 310 50 345 68L390 105H145Z" fill="#0f766e"/>
              <path d="M195 68C210 55 300 55 335 70L370 102H155L195 68Z" fill="#e0f2fe" fillOpacity="0.85"/>
              <path d="M435 142L450 147L435 152" stroke="#fef08a" strokeWidth="4" strokeLinecap="round"/>
              <line x1="75" y1="145" x2="60" y2="148" stroke="#ef4444" strokeWidth="6" strokeLinecap="round"/>
              <circle cx="140" cy="165" r="32" fill="#0f172a" stroke="#94a3b8" strokeWidth="6"/>
              <circle cx="140" cy="165" r="14" fill="#14b8a6"/>
              <circle cx="370" cy="165" r="32" fill="#0f172a" stroke="#94a3b8" strokeWidth="6"/>
              <circle cx="370" cy="165" r="14" fill="#14b8a6"/>
              <path d="M30 165H10 M20 150H0 M15 180H2" stroke="#5eead4" strokeWidth="4" strokeLinecap="round" opacity="0.6"/>
            </svg>
          </div>

          <div style={{ color: "#99f6e4", fontSize: "0.85rem" }}>
            Every open spot in the city, spotted in real time.
          </div>
        </div>

        {/* الجانب الأيمن: فورم تسجيل الدخول النظيف والمنحني */}
        <div className="reg-form-side">
          <div className="reg-form-header">
            <h3>Driver Sign In</h3>
            <p>Welcome back! Please enter your details.</p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="reg-form-grid">
              <div className="reg-input-group full-width">
                <label>Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. driver@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>

              <div className="reg-input-group full-width">
                <label>Password</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            {error && <div className="reg-error">{error}</div>}

            <button type="submit" className="reg-submit-btn" disabled={isSubmitting}>
              {isSubmitting ? "Signing In…" : "SIGN IN"}
            </button>

            <div className="reg-footer-link">
              Don't have an account? <Link to="/register">Create Account</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}