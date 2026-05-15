import { Navigate } from 'react-router-dom'
import { homePathForRole, useAuthStore } from '../../stores/authStore'

export function RootRedirect() {
  const access = useAuthStore((s) => s.access)
  const user = useAuthStore((s) => s.user)

  if (!access || !user?.role) {
    return <Navigate to="/login" replace />
  }

  return <Navigate to={homePathForRole(user.role)} replace />
}
