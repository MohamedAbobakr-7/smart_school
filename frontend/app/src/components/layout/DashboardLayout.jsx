import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { navItemsForRole } from '../../config/navigation'
import { Sidebar } from './Sidebar'
import { apiFetch } from '../../lib/api'
import { SmartChatbot } from '../chatbot/SmartChatbot'

function greetingForHour() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardLayout() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const location = useLocation()
  const [unreadCount, setUnreadCount] = useState(0)

  // Fetch profile once on mount to ensure photo_url is available in the auth store
  useEffect(() => {
    let disposed = false
    async function fetchProfile() {
      try {
        const res = await apiFetch('/users/me/')
        if (res.ok) {
          const data = await res.json()
          if (!disposed) {
            const currentUser = useAuthStore.getState().user
            const photoUrl = data.student_profile?.photo_url || currentUser?.photo_url
            useAuthStore.setState({
              user: { ...currentUser, photo_url: photoUrl },
            })
          }
        }
      } catch (e) {
        // ignore
      }
    }
    fetchProfile()
    return () => { disposed = true }
  }, [])

  useEffect(() => {
    let disposed = false
    async function fetchUnread() {
      try {
        const res = await apiFetch('/notifications/?unread=true')
        if (res.ok) {
          const json = await res.json()
          const count = Array.isArray(json) ? json.length : (json.count ?? (json.results ? json.results.length : 0))
          if (!disposed) setUnreadCount(count)
        }
      } catch (e) {
        // ignore
      }
    }
    fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => {
      disposed = true
      clearInterval(interval)
    }
  }, [location.pathname]) // re-fetch when navigating to/from notifications

  const items = navItemsForRole(user?.role)
  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || 'User'

  const role = user?.role
  const showSmartChatbot = role === 'ADMIN' || role === 'TEACHER' || role === 'STUDENT' || role === 'PARENT'

  return (
    <div className="dashboard-shell">
      <Sidebar items={items} open={menuOpen} onClose={() => setMenuOpen(false)} user={user} />

      <div className="dashboard-main">
        <header className="dashboard-topbar">
          <button
            type="button"
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-label="Open menu"
            onClick={() => setMenuOpen(true)}
          >
            <span className="menu-toggle-bar" />
            <span className="menu-toggle-bar" />
            <span className="menu-toggle-bar" />
          </button>
          <div className="topbar-greeting">
            <span className="topbar-greeting-line">{greetingForHour()}!</span>
            <span className="topbar-greeting-name">{displayName}</span>
          </div>
          <div className="topbar-search-wrap">
            <label className="topbar-search-label" htmlFor="dash-search">
              <span className="visually-hidden">Search</span>
              <svg className="topbar-search-icon" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
                />
              </svg>
              <input
                id="dash-search"
                type="search"
                className="topbar-search"
                placeholder="Search courses, people, reports…"
                autoComplete="off"
              />
            </label>
          </div>
          <div className="topbar-actions">
            <button 
              type="button" 
              className="topbar-icon-btn" 
              aria-label="Notifications"
              style={{ position: 'relative' }}
              onClick={() => navigate(`/${user?.role?.toLowerCase()}/notifications`)}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fill="currentColor"
                  d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z"
                />
              </svg>
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute',
                  top: '-2px',
                  right: '-2px',
                  background: '#ef4444',
                  color: 'white',
                  fontSize: '0.65rem',
                  fontWeight: 'bold',
                  borderRadius: '10px',
                  padding: '2px 6px',
                  border: '2px solid var(--surface-color)',
                  lineHeight: 1
                }}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>
            <span className="topbar-role-pill">{user?.role_display || user?.role}</span>
            <button type="button" className="btn btn-ghost topbar-logout" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </header>

        <main className="dashboard-content">
          <Outlet />
        </main>
      </div>
      {showSmartChatbot ? <SmartChatbot /> : null}
    </div>
  )
}
