import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import "./Register.css";

export default function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    phone: "",
    plate: "",
    vehicleModel: "Car — Sedan",
  });

  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(e) {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccessMsg("");

    if (!formData.fullName.trim() || !formData.email.trim() || !formData.password.trim()) {
      setError("Please fill in all required fields.");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: formData.fullName.trim(),
          email: formData.email.trim(),
          password: formData.password,
          phone_number: formData.phone.trim() || null,
          license_plate: formData.plate.trim() || null,
          car_model: formData.vehicleModel.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed. Please try again.");
      }

      setSuccessMsg("Account created! Redirecting to login…");
      localStorage.setItem("driverName", data.full_name);
      localStorage.setItem("driverEmail", data.email);

      setTimeout(() => {
        navigate("/login");
      }, 1500);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="modern-reg-wrapper">
      <div className="modern-reg-card">
        {/* الجانب الأيسر: اللوجو ورسمة العربية */}
        <div className="reg-visual-side">
          <div className="reg-visual-header">
            <h2>Aswan SmartCurbs</h2>
            <p>Smart Curbside Parking & AI Occupancy</p>
          </div>

          <div className="car-scene">
            {/* رسمة عربية رياضية عصرية SVG بألوان المشروع */}
            <svg className="car-svg" viewBox="0 0 500 220" fill="none" xmlns="http://www.w3.org/2000/svg">
              {/* وهج ولمعان خلف العربية */}
              <circle cx="250" cy="110" r="120" fill="#14b8a6" fillOpacity="0.15" filter="blur(20px)" />
              {/* جسم العربية */}
              <path d="M70 140C90 140 105 110 140 100C190 85 280 85 340 105C380 115 410 125 440 135C455 140 460 155 450 165C430 175 100 175 70 165C55 160 55 140 70 140Z" fill="#14b8a6"/>
              <path d="M145 105L195 65C215 50 310 50 345 68L390 105H145Z" fill="#0f766e"/>
              {/* زجاج العربية */}
              <path d="M195 68C210 55 300 55 335 70L370 102H155L195 68Z" fill="#e0f2fe" fillOpacity="0.85"/>
              {/* الكشافات والخطوط الجمالية */}
              <path d="M435 142L450 147L435 152" stroke="#fef08a" strokeWidth="4" strokeLinecap="round"/>
              <line x1="75" y1="145" x2="60" y2="148" stroke="#ef4444" strokeWidth="6" strokeLinecap="round"/>
              {/* العجلات */}
              <circle cx="140" cy="165" r="32" fill="#0f172a" stroke="#94a3b8" strokeWidth="6"/>
              <circle cx="140" cy="165" r="14" fill="#14b8a6"/>
              <circle cx="370" cy="165" r="32" fill="#0f172a" stroke="#94a3b8" strokeWidth="6"/>
              <circle cx="370" cy="165" r="14" fill="#14b8a6"/>
              {/* خطوط السرعة التفاعلية */}
              <path d="M30 165H10 M20 150H0 M15 180H2" stroke="#5eead4" strokeWidth="4" strokeLinecap="round" opacity="0.6"/>
            </svg>
          </div>

          <div style={{ color: "#99f6e4", fontSize: "0.85rem" }}>
            Reserve, navigate, and park in seconds.
          </div>
        </div>

        {/* الجانب الأيمن: الفورم بالشكل المنحني الأبيض */}
        <div className="reg-form-side">
          <div className="reg-form-header">
            <h3>Driver Registration</h3>
            <p>Welcome to Aswan SmartCurbs</p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="reg-form-grid">
              <div className="reg-input-group full-width">
                <label>Full Name *</label>
                <input
                  name="fullName"
                  type="text"
                  placeholder="e.g. Mahmoud Ali"
                  value={formData.fullName}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="reg-input-group">
                <label>Email Address *</label>
                <input
                  name="email"
                  type="email"
                  placeholder="name@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="reg-input-group">
                <label>Phone Number</label>
                <input
                  name="phone"
                  type="tel"
                  placeholder="+20 100 000 0000"
                  value={formData.phone}
                  onChange={handleChange}
                />
              </div>

              <div className="reg-input-group">
                <label>License Plate</label>
                <input
                  name="plate"
                  type="text"
                  placeholder="e.g. ASW 1234"
                  value={formData.plate}
                  onChange={handleChange}
                />
              </div>

              <div className="reg-input-group">
                <label>Vehicle Model</label>
                <input
                  name="vehicleModel"
                  type="text"
                  placeholder="e.g. Car — Sedan"
                  value={formData.vehicleModel}
                  onChange={handleChange}
                />
              </div>

              <div className="reg-input-group">
                <label>Password *</label>
                <input
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="reg-input-group">
                <label>Confirm Password *</label>
                <input
                  name="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            {error && <div className="reg-error">{error}</div>}
            {successMsg && <div className="reg-success">{successMsg}</div>}

            <button type="submit" className="reg-submit-btn" disabled={isSubmitting}>
              {isSubmitting ? "Creating Account…" : "CREATE ACCOUNT"}
            </button>

            <div className="reg-footer-link">
              Already have an account? <Link to="/login">Sign In</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}