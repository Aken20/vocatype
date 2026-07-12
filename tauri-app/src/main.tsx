import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { PillOverlay } from './components/PillOverlay.tsx'

const isPill = window.location.hash === '#pill'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {isPill ? <PillOverlay /> : <App />}
  </StrictMode>,
)
