import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, MessageSquareText, Send } from 'lucide-react'

import { api, askStream } from '../lib/api'
import { Badge, Button, Card, Citation, EmptyState, ErrorNote, SectionTitle, Spinner } from '../components/ui'

const SUGGESTIONS = [
  'What is the net zero target year, and is it conditional?',
  'How much finance is committed, and to what?',
  'What adaptation measures are proposed for coastal areas?',
  'Which sectors are covered, and which are left out?',
  'How will progress be monitored and verified?',
]

/**
 * Renders an answer with its inline [n] citations turned into anchors that
 * highlight the corresponding source. Without this the citations are just
 * noise in the prose; with it they are the point.
 */
function AnswerText({ text, onCite, activeSource }) {
  const parts = text.split(/(\[\d+(?:\s*,\s*\d+)*\])/g)
  return (
    <p className="whitespace-pre-wrap leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+(?:\s*,\s*\d+)*)\]$/)
        if (!match) return <span key={i}>{part}</span>
        const indices = match[1].split(',').map((n) => Number(n.trim()))
        return (
          <span key={i}>
            {indices.map((n) => (
              <button
                key={n}
                onClick={() => onCite(n - 1)}
                className={`tnum mx-0.5 rounded px-1 text-xs align-super transition ${
                  activeSource === n - 1
                    ? 'bg-[--color-accent] text-white'
                    : 'bg-[--color-accent-soft] text-[--color-accent] hover:bg-[--color-accent] hover:text-white'
                }`}
                title={`Jump to source ${n}`}
              >
                {n}
              </button>
            ))}
          </span>
        )
      })}
    </p>
  )
}

export default function Ask() {
  const [documents, setDocuments] = useState([])
  const [selected, setSelected] = useState([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [activeSource, setActiveSource] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  useEffect(() => {
    api
      .listDocuments()
      .then((docs) => {
        const ready = docs.filter((d) => d.status === 'ready')
        setDocuments(ready)
        setSelected(ready.map((d) => d.id)) // search everything by default
      })
      .catch(setError)
  }, [])

  const toggle = (id) =>
    setSelected((current) => (current.includes(id) ? current.filter((x) => x !== id) : [...current, id]))

  const submit = async (event) => {
    event?.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || selected.length === 0) return

    setBusy(true)
    setError(null)
    setAnswer('')
    setSources([])
    setActiveSource(null)

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await askStream(trimmed, selected, {
        signal: controller.signal,
        onSources: setSources,
        onDelta: (delta) => setAnswer((current) => current + delta),
      })
    } catch (err) {
      if (err.name !== 'AbortError') setError(err)
    } finally {
      setBusy(false)
    }
  }

  if (documents.length === 0) {
    return (
      <EmptyState icon={MessageSquareText} title="No analysed documents">
        Upload a policy in the Library first.
      </EmptyState>
    )
  }

  const grounded = sources.length > 0 && /\[\d/.test(answer)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ask the library</h1>
        <p className="mt-1 text-[--color-muted]">
          Hybrid retrieval finds the relevant passages; the answer cites them by page. Claims without a
          citation are flagged rather than presented as fact.
        </p>
      </div>

      <Card className="p-4">
        <SectionTitle hint={`${selected.length} of ${documents.length} selected`}>Search scope</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {documents.map((doc) => (
            <button
              key={doc.id}
              onClick={() => toggle(doc.id)}
              aria-pressed={selected.includes(doc.id)}
              className={`rounded-full border px-3 py-1 text-sm transition ${
                selected.includes(doc.id)
                  ? 'border-[--color-accent] bg-[--color-accent-soft] text-[--color-accent]'
                  : 'border-[--color-line] text-[--color-muted] hover:border-[--color-accent]/40'
              }`}
            >
              {doc.name}
            </button>
          ))}
        </div>
      </Card>

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about targets, finance, adaptation, governance…"
          className="flex-1 rounded-lg border border-[--color-line] bg-[--color-surface] px-4 py-2.5 text-sm focus-visible:outline-2 focus-visible:outline-[--color-accent]"
        />
        <Button type="submit" disabled={busy || !question.trim() || selected.length === 0}>
          <Send className="h-4 w-4" aria-hidden />
          Ask
        </Button>
      </form>

      {!answer && !busy && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setQuestion(suggestion)}
              className="rounded-full border border-[--color-line] px-3 py-1 text-xs text-[--color-muted] transition hover:border-[--color-accent]/40 hover:text-[--color-ink]"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <ErrorNote error={error} />

      {(busy || answer) && (
        <Card className="animate-fade-up p-5">
          <div className="mb-3 flex items-center gap-2">
            <SectionTitle>Answer</SectionTitle>
            {!busy && answer && !grounded && (
              <Badge tone="warn" className="mb-3">
                <AlertTriangle className="h-3 w-3" aria-hidden /> no citations — treat as unsupported
              </Badge>
            )}
          </div>
          {answer ? (
            <AnswerText text={answer} onCite={setActiveSource} activeSource={activeSource} />
          ) : (
            <Spinner label="Retrieving passages" />
          )}
        </Card>
      )}

      {sources.length > 0 && (
        <section>
          <SectionTitle hint={`${sources.length} passages, reranked`}>Sources</SectionTitle>
          <div className="space-y-2">
            {sources.map((source, i) => (
              <Card
                key={`${source.doc_id}-${source.chunk_index}`}
                className={`p-4 transition ${
                  activeSource === i ? 'border-[--color-accent] ring-1 ring-[--color-accent]/20' : ''
                }`}
              >
                <div className="mb-1.5 flex items-center gap-2 text-xs text-[--color-muted]">
                  <span className="tnum flex h-5 w-5 items-center justify-center rounded bg-[--color-accent-soft] font-medium text-[--color-accent]">
                    {i + 1}
                  </span>
                  <span className="font-medium">{source.document_name}</span>
                  <Citation page={source.page_start} section={source.section} />
                  {source.section && <span className="truncate">{source.section}</span>}
                </div>
                <p className="text-sm leading-relaxed">{source.text}</p>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
