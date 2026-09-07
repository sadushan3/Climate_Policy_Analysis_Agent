import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Leaf } from 'lucide-react'

import { useAuth } from '../lib/auth-context'
import { Button, Card, ErrorNote } from '../components/ui'

const MIN_PASSWORD_LENGTH = 12

export default function Login() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isRegister = mode === 'register'
  // Send the user back where they were trying to go before being bounced here.
  const destination = location.state?.from ?? '/library'

  const submit = async (event) => {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (isRegister) await register(email, password, displayName)
      else await login(email, password)
      navigate(destination, { replace: true })
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  const passwordTooShort = isRegister && password.length > 0 && password.length < MIN_PASSWORD_LENGTH

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center">
      <div className="mb-6 text-center">
        <Leaf className="mx-auto h-8 w-8 text-[--color-accent]" aria-hidden />
        <h1 className="mt-3 text-2xl font-semibold tracking-tight">Climate Policy Intelligence</h1>
        <p className="mt-1 text-sm text-[--color-muted]">
          {isRegister ? 'Create an account to build your document library.' : 'Sign in to your library.'}
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={submit} className="space-y-4">
          {isRegister && (
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Name</span>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                autoComplete="name"
                className="w-full rounded-lg border border-[--color-line] px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-[--color-accent]"
              />
            </label>
          )}

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              className="w-full rounded-lg border border-[--color-line] px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-[--color-accent]"
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block text-sm font-medium">Password</span>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              className="w-full rounded-lg border border-[--color-line] px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-[--color-accent]"
            />
            {isRegister && (
              <span
                className={`mt-1.5 block text-xs ${
                  passwordTooShort ? 'text-[--color-danger]' : 'text-[--color-muted]'
                }`}
              >
                At least {MIN_PASSWORD_LENGTH} characters. Length matters far more than symbols —
                a passphrase of ordinary words is stronger than a short scramble.
              </span>
            )}
          </label>

          <ErrorNote error={error} />

          <Button type="submit" disabled={busy || passwordTooShort} className="w-full">
            {busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
          </Button>
        </form>

        <p className="mt-5 border-t border-[--color-line] pt-4 text-center text-sm text-[--color-muted]">
          {isRegister ? 'Already have an account?' : 'No account yet?'}{' '}
          <button
            onClick={() => {
              setMode(isRegister ? 'login' : 'register')
              setError(null)
            }}
            className="font-medium text-[--color-accent] hover:underline"
          >
            {isRegister ? 'Sign in' : 'Create one'}
          </button>
        </p>
      </Card>
    </div>
  )
}
