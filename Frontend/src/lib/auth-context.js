/**
 * The auth context and its hook, kept separate from the provider component.
 *
 * React Fast Refresh only preserves state for modules that export components
 * exclusively. Mixing the `useAuth` hook into the provider file breaks hot
 * reloading for the whole app, so the non-component exports live here.
 */
import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}
