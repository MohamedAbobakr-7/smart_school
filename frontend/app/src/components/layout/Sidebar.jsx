import { NavLink } from 'react-router-dom'

function initialsFromUser(user) {
  const first = user?.first_name?.trim?.()
  const last = user?.last_name?.trim?.()
  if (first && last) return `${first[0]}${last[0]}`.toUpperCase()
  if (first) return first.slice(0, 2).toUpperCase()
  const u = user?.username?.trim?.()
  if (u) return u.slice(0, 2).toUpperCase()
  return 'SS'
}

export function Sidebar({ items, open, onClose, user }) {
  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || 'User'
  const roleLabel = user?.role_display || user?.role || ''

  return (
    <>
      <button
        type="button"
        className={`sidebar-backdrop ${open ? 'is-open' : ''}`}
        aria-label="Close menu"
        onClick={onClose}
      />
      <aside className={`sidebar ${open ? 'is-open' : ''}`} aria-label="Main navigation">
        <div className="sidebar-profile">
          {user?.photo_url ? (
            <img
              className="sidebar-avatar sidebar-avatar-photo"
              src={user.photo_url}
              alt={displayName}
            />
          ) : (
            <div className="sidebar-avatar" aria-hidden="true">
              {initialsFromUser(user)}
            </div>
          )}
          <div className="sidebar-profile-text">
            <span className="sidebar-profile-name">{displayName}</span>
            {roleLabel ? <span className="sidebar-profile-role">{roleLabel}</span> : null}
          </div>
        </div>
        <nav className="sidebar-nav">
          {items.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `sidebar-link${isActive ? ' is-active' : ''}`}
              onClick={onClose}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="sidebar-footer-mark" aria-hidden="true">
            🌿
          </span>
          <span className="sidebar-footer-text">Smart School</span>
        </div>
      </aside>
    </>
  )
}
