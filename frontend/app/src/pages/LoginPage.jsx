import { useState } from 'react'
import { useLocation, useNavigate, Navigate } from 'react-router-dom'
import { homePathForRole, useAuthStore } from '../stores/authStore'

/** Inline illustration: dashboard + attendance + school figures (no raster assets). */
function LoginAsideIllustration() {
  return (
    <svg
      className="login-aside-illustration"
      viewBox="0 0 320 168"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="login-ill-bar" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fafaf9" stopOpacity="0.38" />
          <stop offset="100%" stopColor="#fafaf9" stopOpacity="0.1" />
        </linearGradient>
        <linearGradient id="login-ill-accent" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#a5b4fc" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.38" />
        </linearGradient>
      </defs>
      {/* Dashboard card */}
      <rect
        x="4"
        y="18"
        width="168"
        height="142"
        rx="14"
        fill="#fafaf9"
        fillOpacity="0.05"
        stroke="#fafaf9"
        strokeOpacity="0.1"
        strokeWidth="1"
      />
      <rect x="22" y="36" width="64" height="5" rx="2.5" fill="#fafaf9" fillOpacity="0.18" />
      <rect x="22" y="46" width="40" height="5" rx="2.5" fill="#fafaf9" fillOpacity="0.1" />
      {/* Sparkline / trend */}
      <path
        d="M22 104 L42 92 L58 98 L78 82 L98 88 L118 76"
        stroke="#fafaf9"
        strokeOpacity="0.22"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Bars */}
      <rect x="26" y="118" width="12" height="28" rx="3" fill="url(#login-ill-bar)" />
      <rect x="46" y="102" width="12" height="44" rx="3" fill="url(#login-ill-bar)" />
      <rect x="66" y="110" width="12" height="36" rx="3" fill="url(#login-ill-bar)" />
      <rect x="86" y="94" width="12" height="52" rx="3" fill="url(#login-ill-accent)" />
      <rect x="106" y="108" width="12" height="38" rx="3" fill="url(#login-ill-bar)" />
      {/* Attendance row */}
      <rect x="22" y="64" width="132" height="22" rx="8" fill="#fafaf9" fillOpacity="0.04" />
      <circle cx="34" cy="75" r="5" stroke="#fafaf9" strokeOpacity="0.25" strokeWidth="1.2" />
      <path d="M31.5 75 L33.5 77.5 L38 72.5" stroke="#fafaf9" strokeOpacity="0.4" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="48" y="71" width="48" height="4" rx="2" fill="#fafaf9" fillOpacity="0.14" />
      <rect x="48" y="78" width="32" height="3" rx="1.5" fill="#fafaf9" fillOpacity="0.08" />
      {/* Teacher / student silhouettes */}
      <g opacity="0.85">
        <ellipse cx="248" cy="44" rx="18" ry="18" fill="#fafaf9" fillOpacity="0.12" />
        <path
          d="M248 64 C228 64 218 88 216 118 L280 118 C278 88 268 64 248 64Z"
          fill="#fafaf9"
          fillOpacity="0.07"
        />
        <rect x="232" y="118" width="32" height="4" rx="2" fill="#fafaf9" fillOpacity="0.06" />
        <ellipse cx="288" cy="52" rx="14" ry="14" fill="#fafaf9" fillOpacity="0.1" />
        <path
          d="M288 68 C276 68 268 84 266 108 L310 108 C308 84 300 68 288 68Z"
          fill="#fafaf9"
          fillOpacity="0.06"
        />
        <rect x="276" y="108" width="24" height="3" rx="1.5" fill="#fafaf9" fillOpacity="0.05" />
      </g>
      {/* Floating stat chip */}
      <rect x="196" y="28" width="112" height="36" rx="10" fill="#fafaf9" fillOpacity="0.06" stroke="#fafaf9" strokeOpacity="0.08" />
      <rect x="208" y="42" width="36" height="6" rx="3" fill="#fafaf9" fillOpacity="0.12" />
      <rect x="252" y="40" width="44" height="14" rx="4" fill="url(#login-ill-accent)" />
    </svg>
  )
}

function IconHelp({ className }) {
  return (
    <svg className={className} width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"
      />
    </svg>
  )
}

function IconSignIn({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M11 7L9.6 8.4l2.6 2.6H3v2h9.2l-2.6 2.6L11 17l5-5-5-5zm8 9h-2V8h2v8z"
        fill="currentColor"
      />
    </svg>
  )
}

function IconEye({ className }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 9a3 3 0 100 6 3 3 0 000-6zm0-4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zm0 12a4.5 4.5 0 110-9 4.5 4.5 0 010 9z"
        fill="currentColor"
      />
    </svg>
  )
}

function IconChevronDown({ className }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M7 10l5 5 5-5H7z" fill="currentColor" />
    </svg>
  )
}

function AsideRings() {
  return (
    <svg className="login-aside-rings" viewBox="0 0 420 420" aria-hidden="true">
      <circle cx="210" cy="210" r="72" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.14" />
      <circle cx="210" cy="210" r="120" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.1" />
      <circle cx="210" cy="210" r="175" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.07" />
      <circle cx="210" cy="210" r="230" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.05" />
    </svg>
  )
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const access = useAuthStore((s) => s.access)
  const user = useAuthStore((s) => s.user)
  const login = useAuthStore((s) => s.login)

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (access && user?.role) {
    return <Navigate to={homePathForRole(user.role)} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await login(username.trim(), password)
      const from = location.state?.from
      const home = homePathForRole(u.role)
      if (from && typeof from === 'string' && (from === home || from.startsWith(`${home}/`))) {
        navigate(from, { replace: true })
      } else {
        navigate(home, { replace: true })
      }
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const year = new Date().getFullYear()

  return (
    <div className="login-page">
      <div className="login-backdrop" aria-hidden="true" />
      <div className="login-mega-card">
        <div className="login-split">
          <aside className="login-aside" aria-hidden="true">
            <AsideRings />
            <div className="login-aside-body">
              <p className="login-aside-tagline">
                Learning, attendance, and grades — one connected platform for your school community.
              </p>
              <div className="login-aside-head-block">
                <h1 className="login-aside-headline">Manage your school</h1>
              </div>
              <div className="login-aside-visual">
                <LoginAsideIllustration />
              </div>
            </div>
            <div className="login-aside-corner" title="Smart School">
              <span className="login-aside-corner-mark">SS</span>
            </div>
          </aside>

          <div className="login-panel">
            <header className="login-panel-header">
              <span className="login-wordmark">Smart School</span>
              <a className="login-panel-help" href="#" onClick={(e) => e.preventDefault()}>
                <IconHelp className="login-panel-help-icon" />
                Help
              </a>
            </header>

            <div className="login-panel-main">
              <form className="login-form" onSubmit={handleSubmit} noValidate>
                <h2 className="login-form-title">Sign In</h2>

                <div className="login-field">
                  <label className="login-label" htmlFor="login-username">
                    Username or student ID
                  </label>
                  <input
                    id="login-username"
                    className="login-input login-input--plain"
                    name="username"
                    autoComplete="username"
                    placeholder="Staff: username · Students: school ID"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                </div>

                <div className="login-field">
                  <label className="login-label" htmlFor="login-password">
                    Password
                  </label>
                  <div className="login-password-wrap">
                    <input
                      id="login-password"
                      className="login-input login-input--plain login-input--with-toggle"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      className={`login-password-toggle${showPassword ? ' is-active' : ''}`}
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      aria-pressed={showPassword}
                    >
                      <IconEye className="login-password-toggle-icon" />
                    </button>
                  </div>
                </div>


                {error ? (
                  <p className="login-error" role="alert">
                    {error}
                  </p>
                ) : null}

                <button type="submit" className="login-submit login-submit--pill" disabled={loading}>
                  <IconSignIn className="login-submit-icon" />
                  {loading ? 'Signing in…' : 'Sign In'}
                </button>
              </form>
            </div>

            <footer className="login-panel-footer">
              <span className="login-footer-copy">© {year} Smart School</span>
              <div className="login-footer-links">
                <a className="login-footer-link" href="#" onClick={(e) => e.preventDefault()}>
                  Contact us
                </a>
                <button type="button" className="login-footer-lang">
                  English
                  <IconChevronDown className="login-footer-lang-chevron" />
                </button>
              </div>
            </footer>
          </div>
        </div>
      </div>
    </div>
  )
}
