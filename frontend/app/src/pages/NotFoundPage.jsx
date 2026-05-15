import { Link } from 'react-router-dom'
import { homePathForRole, useAuthStore } from '../stores/authStore'

export function NotFoundPage() {
  const user = useAuthStore((s) => s.user)
  const access = useAuthStore((s) => s.access)
  const home = access && user?.role ? homePathForRole(user.role) : '/login'

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-narrow">
        <h1 className="auth-title">Page not found</h1>
        <p className="muted">The page you requested does not exist.</p>
        <Link className="btn btn-primary btn-block" to={home}>
          {access ? 'Back to dashboard' : 'Sign in'}
        </Link>
      </div>
    </div>
  )
}
