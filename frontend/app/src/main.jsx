import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './i18n'              // ← initialize i18next before App renders
import './index.css'
import './styles/dashboard-app.css'
import './styles/dashboard-analytics.css'
import App from './App.jsx'
import { useLangStore } from './stores/langStore'

// Sync document dir/lang with persisted preference on first load
useLangStore.getState().initLang()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
