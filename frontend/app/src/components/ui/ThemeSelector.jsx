import { useState, useRef, useEffect } from 'react'
import { useThemeStore } from '../../stores/themeStore'

const THEME_OPTIONS = [
  { value: 'default', label: 'Default', icon: '☀️' },
  { value: 'dark',    label: 'Dark',    icon: '🌙' },
]

export function ThemeSelector() {
  const theme = useThemeStore((s) => s.theme)
  const setTheme = useThemeStore((s) => s.setTheme)
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const current = THEME_OPTIONS.find((o) => o.value === theme) || THEME_OPTIONS[0]

  return (
    <div className="theme-selector" ref={ref}>
      <button
        type="button"
        className="theme-selector-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="listbox"
        title={`Current theme: ${current.label}`}
      >
        <span className="theme-selector-icon">{current.icon}</span>
        <span className="theme-selector-label">{current.label}</span>
        <svg className="theme-selector-chevron" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">
          <path d="M3 4.5L6 7.5L9 4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      {open && (
        <ul className="theme-selector-menu" role="listbox" aria-label="Select theme">
          {THEME_OPTIONS.map((opt) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={opt.value === theme}
              className={`theme-selector-option${opt.value === theme ? ' is-active' : ''}`}
              onClick={() => {
                setTheme(opt.value)
                setOpen(false)
              }}
            >
              <span className="theme-selector-option-icon">{opt.icon}</span>
              <span className="theme-selector-option-label">{opt.label}</span>
              {opt.value === theme && (
                <svg className="theme-selector-option-check" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
                  <path d="M3 7L6 10L11 4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
