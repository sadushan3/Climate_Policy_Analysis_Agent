/**
 * Authentication state.
 *
 * The access token is held in memory only — never localStorage. A token in
 * localStorage is readable by any script on the page, so a single XSS bug hands
 * an attacker a working session. Durability instead comes from the HttpOnly
 * refresh cookie the API sets: on page load we call /refresh once, and if the
 * cookie is still valid we silently get a new access token back.
 *
 * The cost of that choice is one extra request on boot. The benefit is that a
 * script injection cannot read the long-lived credential.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'

import { api, setAccessToken } from './api'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // `booting` distinguishes "we haven't checked yet" from "checked, signed out".
  // Without it the app flashes the login screen on every refresh.
  const [booting, setBooting] = useState(true)

  const applySession = useCallback((session) => {
    setAccessToken(session.access_token, session.expires_in)
    setUser(session.user)
    return session.user
  }, [])

  useEffect(() => {
    let cancelled = false
    api
      .refresh()
      .then((session) => !cancelled && applySession(session))
      .catch(() => {
        // No valid refresh cookie: a normal signed-out visit, not an error.
      })
      .finally(() => !cancelled && setBooting(false))
    return () => {
      cancelled = true
    }
  }, [applySession])

  const value = useMemo(
    () => ({
      user,
      booting,
      isAuthenticated: Boolean(user),
      login: async (email, password) => applySession(await api.login(email, password)),
      register: async (email, password, displayName) =>
        applySession(await api.register(email, password, displayName)),
      logout: async () => {
        try {
          await api.logout()
        } finally {
          setAccessToken(null)
          setUser(null)
        }
      },
      logoutEverywhere: async () => {
        try {
          await api.logoutEverywhere()
        } finally {
          setAccessToken(null)
          setUser(null)
        }
      },
    }),
    [user, booting, applySession],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}