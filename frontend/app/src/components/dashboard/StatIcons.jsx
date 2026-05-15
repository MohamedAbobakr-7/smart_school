/** Minimal inline icons for stat cards */

function Svg({ children, className }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {children}
    </svg>
  )
}

export function StatIcon({ name, className = '' }) {
  const c = `dash-stat-icon-svg ${className}`.trim()
  switch (name) {
    case 'users':
      return (
        <Svg className={c}>
          <circle cx="9" cy="8" r="3" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <circle cx="16" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.6" fill="none" />
          <path
            d="M4 19v-1a4 4 0 014-4h2a4 4 0 014 4v1M15 19v-1a3 3 0 013-3"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            fill="none"
          />
        </Svg>
      )
    case 'graduation':
      return (
        <Svg className={c}>
          <path d="M12 4L4 8l8 4 8-4-8-4z" fill="currentColor" opacity="0.9" />
          <path d="M6 10v5c0 2 2.5 4 6 4s6-2 6-4v-5" stroke="currentColor" strokeWidth="1.8" fill="none" />
        </Svg>
      )
    case 'calendar':
      return (
        <Svg className={c}>
          <rect x="4" y="5" width="16" height="15" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M8 3v4M16 3v4M4 11h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </Svg>
      )
    case 'document':
      return (
        <Svg className={c}>
          <path
            d="M8 4h6l4 4v12a1 1 0 01-1 1H8a1 1 0 01-1-1V5a1 1 0 011-1z"
            stroke="currentColor"
            strokeWidth="1.8"
            fill="none"
          />
          <path d="M14 4v4h4" stroke="currentColor" strokeWidth="1.8" />
          <path d="M9 13h6M9 17h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </Svg>
      )
    case 'layers':
      return (
        <Svg className={c}>
          <path d="M12 3L4 7l8 4 8-4-8-4z" fill="currentColor" opacity="0.85" />
          <path d="M4 12l8 4 8-4M4 17l8 4 8-4" stroke="currentColor" strokeWidth="1.8" fill="none" />
        </Svg>
      )
    case 'camera':
      return (
        <Svg className={c}>
          <rect x="4" y="7" width="16" height="12" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <circle cx="12" cy="13" r="3" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M9 7V5h6v2" stroke="currentColor" strokeWidth="1.8" />
        </Svg>
      )
    case 'chart':
      return (
        <Svg className={c}>
          <path d="M4 19h16M7 16V10M12 16V6M17 16v-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </Svg>
      )
    case 'check':
      return (
        <Svg className={c}>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M9 12l2 2 4-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </Svg>
      )
    case 'clock':
      return (
        <Svg className={c}>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M12 8v5l3 2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </Svg>
      )
    case 'play':
      return (
        <Svg className={c}>
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M11 9l5 3-5 3V9z" fill="currentColor" />
        </Svg>
      )
    case 'heart':
      return (
        <Svg className={c}>
          <path
            d="M12 20s-7-4.6-7-10a5 5 0 019-2.5A5 5 0 0119 10c0 5.4-7 10-7 10z"
            stroke="currentColor"
            strokeWidth="1.8"
            fill="none"
            strokeLinejoin="round"
          />
        </Svg>
      )
    case 'bell':
      return (
        <Svg className={c}>
          <path d="M6 16h12l-1.5-2V10a4.5 4.5 0 10-9 0v4L6 16z" stroke="currentColor" strokeWidth="1.8" fill="none" />
          <path d="M10 20h4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </Svg>
      )
    default:
      return (
        <Svg className={c}>
          <path d="M12 3l1.5 5h5l-4 3 1.5 5L12 14l-4.5 3L9 11l-4-3h5L12 3z" fill="currentColor" opacity="0.85" />
        </Svg>
      )
  }
}
