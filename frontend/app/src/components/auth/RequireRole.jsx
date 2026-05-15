import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'

/**
 * Wraps a layout route: requires JWT + user role in `roles`.
 */
export function RequireRole({ roles, children }) {
  const access = useAuthStore((s) => s.access)
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!access || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (!roles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />
  }

  return children
}
