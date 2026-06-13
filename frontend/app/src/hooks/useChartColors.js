import { useEffect, useState } from 'react'
import { useThemeStore } from '../stores/themeStore'

/** Read resolved CSS variable values for chart rendering.
 *  Recharts props need real color strings, not var(--*) references,
 *  so we read the computed values whenever the theme changes. */
export function useChartColors() {
  const theme = useThemeStore((s) => s.theme)
  const [colors, setColors] = useState({})
  useEffect(() => {
    const cs = getComputedStyle(document.documentElement)
    setColors({
      areaStroke:    cs.getPropertyValue('--ss-chart-area-stroke').trim(),
      areaFill:      cs.getPropertyValue('--ss-chart-area-fill').trim(),
      barFill:       cs.getPropertyValue('--ss-chart-bar-fill').trim(),
      cursorFill:    cs.getPropertyValue('--ss-chart-cursor').trim(),
      gridStroke:    cs.getPropertyValue('--ss-chart-grid').trim(),
      tickFill:      cs.getPropertyValue('--ss-text-muted').trim(),
      dotStroke:     cs.getPropertyValue('--ss-bg-card').trim(),
      cursorStroke:  cs.getPropertyValue('--ss-scrollbar-thumb').trim(),
      primary:       cs.getPropertyValue('--ss-primary').trim(),
      primaryDeep:   cs.getPropertyValue('--ss-primary-deep').trim(),
      primaryEnd:    cs.getPropertyValue('--ss-primary-end').trim(),
      primaryLight:  cs.getPropertyValue('--ss-primary-light').trim(),
      primaryShadow: cs.getPropertyValue('--ss-primary-shadow').trim(),
      successBold:   cs.getPropertyValue('--ss-success-bold').trim(),
      dangerBold:    cs.getPropertyValue('--ss-danger-bold').trim(),
      warningBold:   cs.getPropertyValue('--ss-warning-bold').trim(),
    })
  }, [theme])
  return colors
}
