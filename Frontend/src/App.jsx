import { Suspense, lazy, useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { GitCompareArrows, Library as LibraryIcon, LogOut, MessageSquareText, Sparkles } from 'lucide-react'

import { api, onSessionExpired } from './lib/api'
import { useAuth } from './lib/auth-context'
import { Spinner } from './components/ui'
import Library from './pages/Library'
import Login from './pages/Login'

// Recharts is ~400 kB and only two routes need it. Loading those routes lazily
// keeps it out of the initial bundle, so the landing route (Library, which has
// no charts) is interactive without paying for the charting library.
const DocumentDetail = lazy(() => import('./pages/DocumentDetail'))
const Compare = lazy(() => import('./pages/Compare'))
const Ask = lazy(() => import('./pages/Ask'))

const NAV = [
  { to: '/library', label: 'Library', icon: LibraryIcon },
  { to: '/compare', label: 'Compare', icon: GitCompareArrows },
  { to: '/ask', label: 'Ask', icon: MessageSquareText },
]

/**
 * Surfaces backend capability in the header.
 *
 * The app works without an LLM key, but the *user* needs to know which mode
 * they are in — otherwise "no narrative was generated" reads as a bug.
 */
function LlmStatus() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    let cancelled = false
    api
      .health()
      .then((data) => !cancelled && setHealth(data))
      .catch(() => !cancelled && setHealth({ status: 'unreachable' }))
    return () => {
      cancelled = true
    }
  }, [])

  if (!health) return null

  if (health.status === 'unreachable') {
    return (
      <span className="rounded-full border border-[--color-danger]/25 bg-[--color-danger-soft] px-2.5 py-1 text-xs text-[--color-danger]">
        API offline
      </span>
    )
  }

  return health.llm_enabled ? (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-[--color-accent]/20 bg-[--color-accent-soft] px-2.5 py-1 text-xs font-medium text-[--color-accent]"
      title={`Synthesis and grounded Q&A enabled via ${health.llm_model}`}
    >
      <Sparkles className="h-3 w-3" aria-hidden />
      AI synthesis on
    </span>
  ) : (
    <span
      className="rounded-full border border-[--color-line] px-2.5 py-1 text-xs text-[--color-muted]"
      title="Set ANTHROPIC_API_KEY to enable written synthesis and grounded Q&A. All analysis below runs locally either way."
    >
      Local models only
    </span>
  )
}

/** Gate for routes that need a signed-in user. */
function RequireAuth({ children }) {
  const { isAuthenticated, booting } = useAuth()
  const location = useLocation()

  // Without this branch the app would flash the login screen on every reload
  // while the silent refresh is still in flight.
  if (booting) {
    return (
      <div className="flex justify-center py-24">
        <Spinner label="Restoring session" />
      </div>
    )
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return children
}

function UserMenu() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  return (
    <div className="flex items-center gap-3">
      <span className="hidden text-sm text-[--color-muted] sm:inline" title={user.email}>
        {user.display_name || user.email}
      </span>
      <button
        onClick={async () => {
          await logout()
          navigate('/login', { replace: true })
        }}
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-[--color-muted] transition hover:bg-[--color-canvas] hover:text-[--color-ink]"
      >
        <LogOut className="h-4 w-4" aria-hidden />
        <span className="hidden sm:inline">Sign out</span>
      </button>
    </div>
  )
}

export default function App() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // When a refresh fails, the API client tells us the session is gone; bounce to
  // the login screen rather than leaving the page erroring in place.
  useEffect(() => {
    onSessionExpired(() => navigate('/login', { replace: true }))
  }, [navigate])

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-[--color-line] bg-[--color-surface]/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-3">
          <NavLink to="/library" className="flex items-baseline gap-2">
            <span className="font-semibold tracking-tight">Climate Policy Intelligence</span>
          </NavLink>

          {isAuthenticated && (
            <nav className="flex items-center gap-1">
              {NAV.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    `inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm transition ${
                      isActive
                        ? 'bg-[--color-accent-soft] font-medium text-[--color-accent]'
                        : 'text-[--color-muted] hover:bg-[--color-canvas] hover:text-[--color-ink]'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {label}
                </NavLink>
              ))}
            </nav>
          )}

          <div className="ml-auto flex items-center gap-3">
            <LlmStatus />
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">
        <Suspense fallback={<Spinner label="Loading" />}>
          <Routes>
            <Route path="/" element={<Navigate to="/library" replace />} />
            <Route path="/login" element={isAuthenticated ? <Navigate to="/library" replace /> : <Login />} />

            <Route
              path="/library"
              element={
                <RequireAuth>
                  <Library />
                </RequireAuth>
              }
            />
            <Route
              path="/documents/:id"
              element={
                <RequireAuth>
                  <DocumentDetail />
                </RequireAuth>
              }
            />
            <Route
              path="/compare"
              element={
                <RequireAuth>
                  <Compare />
                </RequireAuth>
              }
            />
            <Route
              path="/ask"
              element={
                <RequireAuth>
                  <Ask />
                </RequireAuth>
              }
            />

            <Route path="*" element={<Navigate to="/library" replace />} />
          </Routes>
        </Suspense>
      </main>

      <footer className="border-t border-[--color-line] px-6 py-5 text-center text-xs text-[--color-muted]">
        Hybrid retrieval over local embedding models, with optional Claude synthesis. Every claim is
        traceable to a page.
      </footer>
    </div>
  )
}
