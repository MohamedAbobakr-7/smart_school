import { Link } from 'react-router-dom'
import { homePathForRole, useAuthStore } from '../stores/authStore'

export function UnauthorizedPage() {
  const user = useAuthStore((s) => s.user)
  const access = useAuthStore((s) => s.access)
  const home = user?.role ? homePathForRole(user.role) : '/login'

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-narrow">
        <h1 className="auth-title">Access denied</h1>
        <p className="muted">You don&apos;t have permission to view this page.</p>
        {access ? (
          <Link className="btn btn-primary btn-block" to={home}>
            Go to my dashboard
          </Link>
        ) : (
          <Link className="btn btn-primary btn-block" to="/login">
            Sign in
          </Link>
        )}
      </div>
    </div>
  )
}
