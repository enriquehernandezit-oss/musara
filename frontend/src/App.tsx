import { createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Landing from './pages/Landing'
import Callback from './pages/Callback'
import Build from './pages/Build'

// ── Auth context ──────────────────────────────────────────────────────────────
type AuthCtx = ReturnType<typeof useAuth>
const AuthContext = createContext<AuthCtx | null>(null)
export const useAuthCtx = () => useContext(AuthContext)!

function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>
}

// ── Route guard ───────────────────────────────────────────────────────────────
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { ready, isAuthenticated } = useAuthCtx()
  if (!ready) return <PageLoader />
  if (!isAuthenticated) return <Navigate to="/" replace />
  return <>{children}</>
}

function PageLoader() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: "'Bebas Neue', sans-serif",
          fontSize: '2rem',
          letterSpacing: '0.08em',
          color: 'var(--text-3)',
          marginBottom: '1rem',
        }}>MUSARA</div>
        <div className="spinner" style={{ margin: '0 auto' }} />
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/"          element={<LandingGate />} />
          <Route path="/callback"  element={<Callback />} />
          <Route path="/build"     element={<RequireAuth><Build /></RequireAuth>} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

// Redirect authed users straight to /build
function LandingGate() {
  const { ready, isAuthenticated } = useAuthCtx()
  if (!ready) return <PageLoader />
  if (isAuthenticated) return <Navigate to="/build" replace />
  return <Landing />
}
