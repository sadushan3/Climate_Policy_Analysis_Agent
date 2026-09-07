/**
 * API client.
 *
 * One module owns every call to the backend, so error shape, base URL and
 * streaming behaviour are handled in exactly one place. Components never touch
 * fetch directly.
 */

const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

// The access token lives in a module variable, never in localStorage -- see
// lib/auth.jsx for why. `credentials: "include"` on every call carries the
// HttpOnly refresh cookie that makes the session survive a reload.
let accessToken = null
let onSessionLost = null

export function setAccessToken(token) {
  accessToken = token
}

export function onSessionExpired(handler) {
  onSessionLost = handler
}

export class ApiError extends Error {
  constructor(message, { status, code, details } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

async function rawRequest(path, options = {}) {
  return fetch(`${BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...options.headers,
    },
  })
}

// Only one refresh may be in flight at a time. Without this, a page that fires
// four requests on mount would trigger four concurrent refreshes -- and since
// the server rotates the refresh token on every use, three of them would present
// an already-rotated token and trip the reuse-detection that revokes the session.
let refreshInFlight = null

async function refreshOnce() {
  if (!refreshInFlight) {
    refreshInFlight = rawRequest('/api/v1/auth/refresh', { method: 'POST' })
      .then(async (response) => {
        if (!response.ok) throw new ApiError('Session expired', { status: 401 })
        const session = await response.json()
        accessToken = session.access_token
        return session
      })
      .finally(() => {
        refreshInFlight = null
      })
  }
  return refreshInFlight
}

async function request(path, options = {}, { retryOnAuthFailure = true } = {}) {
  let response
  try {
    response = await rawRequest(path, options)

    // An expired access token is recoverable: refresh and replay once. Auth
    // endpoints are excluded to avoid recursing on a failed login.
    if (
      response.status === 401 &&
      retryOnAuthFailure &&
      !path.startsWith('/api/v1/auth/')
    ) {
      try {
        await refreshOnce()
        response = await rawRequest(path, options)
      } catch {
        onSessionLost?.()
      }
    }
  } catch (cause) {
    // A network-level failure has no status; say so plainly rather than
    // surfacing "Failed to fetch" to the user.
    throw new ApiError('Cannot reach the API. Is the backend running?', { status: 0, cause })
  }

  if (response.status === 204) return null

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const error = body?.error
    throw new ApiError(error?.message ?? `Request failed (${response.status})`, {
      status: response.status,
      code: error?.code,
      details: error?.details,
    })
  }
  return body
}

const json = (payload) => ({ method: 'POST', body: JSON.stringify(payload) })

export const api = {
  health: () => request('/health'),
  taxonomy: () => request('/api/v1/taxonomy'),

  register: (email, password, display_name = '') =>
    request('/api/v1/auth/register', json({ email, password, display_name })),
  login: (email, password) => request('/api/v1/auth/login', json({ email, password })),
  refresh: () => request('/api/v1/auth/refresh', { method: 'POST' }, { retryOnAuthFailure: false }),
  logout: () => request('/api/v1/auth/logout', { method: 'POST' }),
  logoutEverywhere: () => request('/api/v1/auth/logout-all', { method: 'POST' }),
  me: () => request('/api/v1/auth/me'),

  listDocuments: () => request('/api/v1/documents'),
  getDocument: (id) => request(`/api/v1/documents/${id}`),
  deleteDocument: (id) => request(`/api/v1/documents/${id}`, { method: 'DELETE' }),

  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/api/v1/documents', { method: 'POST', body: form })
  },

  getJob: (id) => request(`/api/v1/jobs/${id}`),
  getJobResult: (id) => request(`/api/v1/jobs/${id}/result`),

  compare: (docIdA, docIdB) => request('/api/v1/compare', json({ doc_id_a: docIdA, doc_id_b: docIdB })),
  search: (query, docIds, topK = 8) => request('/api/v1/search', json({ query, doc_ids: docIds, top_k: topK })),
  ask: (question, docIds, topK) => request('/api/v1/ask', json({ question, doc_ids: docIds, top_k: topK })),
}

/**
 * Follow a background job to completion.
 *
 * Prefers the server-sent-event stream and falls back to polling, because SSE
 * is the thing most likely to be broken by a corporate proxy and a stuck
 * progress bar is a worse failure than a slightly chattier client.
 */
export function followJob(jobId, { onProgress, signal } = {}) {
  return new Promise((resolve, reject) => {
    let settled = false
    const finish = (fn, value) => {
      if (settled) return
      settled = true
      clearInterval(poller)
      fn(value)
    }

    // The job endpoints require a bearer token and the browser `EventSource`
    // API cannot set headers, so the UI polls rather than streaming. Putting
    // the token in the URL would make SSE work but would also write a live
    // credential into access logs and browser history, which is a bad trade for
    // a progress bar. `GET /jobs/{id}/stream` remains available to non-browser
    // clients that can send the header.
    const poller = setInterval(async () => {
      try {
        const state = await api.getJob(jobId)
        onProgress?.(state)
        if (state.status === 'succeeded') {
          const { result } = await api.getJobResult(jobId)
          finish(resolve, result)
        } else if (state.status === 'failed') {
          finish(reject, new ApiError(state.error ?? 'Job failed'))
        }
      } catch (error) {
        finish(reject, error)
      }
    }, 1200)

    signal?.addEventListener('abort', () => finish(reject, new DOMException('Aborted', 'AbortError')))
  })
}

/** Stream a grounded answer, yielding sources first then text deltas. */
export async function askStream(question, docIds, { onSources, onDelta, signal } = {}) {
  const response = await rawRequest('/api/v1/ask/stream', {
    method: 'POST',
    body: JSON.stringify({ question, doc_ids: docIds }),
    signal,
  })
  if (!response.ok || !response.body) throw new ApiError('Streaming failed', { status: response.status })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE frames are separated by a blank line; the last fragment may be partial.
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''

    for (const frame of frames) {
      const line = frame.split('\n').find((l) => l.startsWith('data: '))
      if (!line) continue
      const message = JSON.parse(line.slice(6))
      if (message.type === 'sources') onSources?.(message.payload)
      else if (message.type === 'delta') onDelta?.(message.payload)
      else if (message.type === 'error') throw new ApiError(message.payload)
    }
  }
}
