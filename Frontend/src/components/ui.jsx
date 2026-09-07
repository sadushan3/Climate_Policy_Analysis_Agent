/**
 * Shared presentational primitives.
 *
 * Kept in one file because they are small and always used together; splitting
 * eight ten-line components across eight files costs more than it explains.
 */
import { AlertCircle, Inbox, Loader2 } from 'lucide-react'

export function Card({ className = '', children, ...props }) {
  return (
    <div
      className={`rounded-xl border border-[--color-line] bg-[--color-surface] ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function SectionTitle({ children, hint }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-[--color-muted]">{children}</h2>
      {hint && <span className="text-xs text-[--color-muted]">{hint}</span>}
    </div>
  )
}

const TONES = {
  neutral: 'bg-[--color-canvas] text-[--color-muted] border-[--color-line]',
  accent: 'bg-[--color-accent-soft] text-[--color-accent] border-[--color-accent]/20',
  warn: 'bg-[--color-warn-soft] text-[--color-warn] border-[--color-warn]/20',
  danger: 'bg-[--color-danger-soft] text-[--color-danger] border-[--color-danger]/20',
}

export function Badge({ tone = 'neutral', children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}

export function Button({ variant = 'primary', className = '', disabled, children, ...props }) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ' +
    'disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 ' +
    'focus-visible:outline-[--color-accent]'
  const variants = {
    primary: 'bg-[--color-accent] text-white hover:bg-[--color-accent]/90',
    secondary: 'border border-[--color-line] bg-[--color-surface] hover:bg-[--color-canvas]',
    ghost: 'text-[--color-muted] hover:bg-[--color-canvas] hover:text-[--color-ink]',
    danger: 'border border-[--color-danger]/30 text-[--color-danger] hover:bg-[--color-danger-soft]',
  }
  return (
    <button className={`${base} ${variants[variant]} ${className}`} disabled={disabled} {...props}>
      {children}
    </button>
  )
}

export function Spinner({ label = 'Loading', className = '' }) {
  return (
    <span className={`inline-flex items-center gap-2 text-sm text-[--color-muted] ${className}`}>
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
      <span>{label}</span>
    </span>
  )
}

export function ErrorNote({ error, className = '' }) {
  if (!error) return null
  return (
    <div
      role="alert"
      className={`flex items-start gap-2 rounded-lg border border-[--color-danger]/25 bg-[--color-danger-soft] px-3 py-2 text-sm text-[--color-danger] ${className}`}
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span>{error.message ?? String(error)}</span>
    </div>
  )
}

export function EmptyState({ icon: Icon = Inbox, title, children, action }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-[--color-line] px-6 py-14 text-center">
      <Icon className="h-7 w-7 text-[--color-muted]" aria-hidden />
      <p className="font-medium">{title}</p>
      {children && <p className="max-w-sm text-sm text-[--color-muted]">{children}</p>}
      {action}
    </div>
  )
}

/** A labelled proportion bar. Width is a share in [0, 1]. */
export function Meter({ value, tone = 'accent', className = '' }) {
  const pct = Math.max(0, Math.min(1, value ?? 0)) * 100
  const colour = tone === 'accent' ? 'bg-[--color-accent]' : 'bg-[--color-muted]'
  return (
    <div className={`h-1.5 w-full overflow-hidden rounded-full bg-[--color-line] ${className}`}>
      <div className={`h-full rounded-full ${colour}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function Stat({ label, value, hint }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-[--color-muted]">{label}</div>
      <div className="tnum mt-1 text-2xl font-semibold">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-[--color-muted]">{hint}</div>}
    </div>
  )
}

/**
 * A page-number chip. Every factual claim the app renders traces back to one of
 * these, which is the whole point of the citation pipeline.
 */
export function Citation({ page, section, className = '' }) {
  if (!page) return null
  return (
    <span
      className={`tnum inline-flex shrink-0 items-center rounded border border-[--color-line] bg-[--color-canvas] px-1.5 py-0.5 text-[11px] text-[--color-muted] ${className}`}
      title={section || undefined}
    >
      p.{page}
    </span>
  )
}
