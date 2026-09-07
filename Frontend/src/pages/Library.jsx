import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Trash2, UploadCloud } from 'lucide-react'

import { api, followJob } from '../lib/api'
import { Badge, Button, Card, EmptyState, ErrorNote, Meter, Spinner } from '../components/ui'

const ACCEPT = '.pdf,.docx,.txt,.md'

function StatusBadge({ status }) {
  const tone = { ready: 'accent', failed: 'danger', processing: 'warn', pending: 'warn' }[status] ?? 'neutral'
  return <Badge tone={tone}>{status}</Badge>
}

function UploadZone({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [queue, setQueue] = useState([])
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const upload = useCallback(
    async (files) => {
      setError(null)
      for (const file of files) {
        const key = `${file.name}-${Date.now()}`
        setQueue((q) => [...q, { key, name: file.name, stage: 'uploading', progress: 0 }])
        try {
          const response = await api.uploadDocument(file)

          if (!response.job_id) {
            // Byte-identical to something already analysed; nothing to wait for.
            setQueue((q) => q.map((i) => (i.key === key ? { ...i, stage: 'already analysed', progress: 1 } : i)))
          } else {
            await followJob(response.job_id, {
              onProgress: (state) =>
                setQueue((q) =>
                  q.map((i) => (i.key === key ? { ...i, stage: state.stage, progress: state.progress } : i)),
                ),
            })
            setQueue((q) => q.map((i) => (i.key === key ? { ...i, stage: 'done', progress: 1 } : i)))
          }
          onUploaded()
        } catch (err) {
          setError(err)
          setQueue((q) => q.filter((i) => i.key !== key))
        }
      }
      // Leave completed rows up briefly so the user sees the outcome.
      setTimeout(() => setQueue((q) => q.filter((i) => i.progress < 1)), 2500)
    },
    [onUploaded],
  )

  const onDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    upload([...event.dataTransfer.files])
  }

  return (
    <div>
      <div
        onDragEnter={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        aria-label="Upload policy documents"
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[--color-accent] ${
          dragging
            ? 'border-[--color-accent] bg-[--color-accent-soft]'
            : 'border-[--color-line] bg-[--color-surface] hover:border-[--color-accent]/50'
        }`}
      >
        <UploadCloud className="h-7 w-7 text-[--color-muted]" aria-hidden />
        <p className="font-medium">Drop policy documents here</p>
        <p className="text-sm text-[--color-muted]">PDF, DOCX, TXT or Markdown — up to 40 MB, several at once</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => {
            upload([...e.target.files])
            e.target.value = ''
          }}
        />
      </div>

      <ErrorNote error={error} className="mt-3" />

      {queue.length > 0 && (
        <div className="mt-3 space-y-2">
          {queue.map((item) => (
            <Card key={item.key} className="px-4 py-3">
              <div className="flex items-center justify-between gap-4 text-sm">
                <span className="truncate font-medium">{item.name}</span>
                <span className="tnum shrink-0 text-xs text-[--color-muted]">
                  {item.stage} · {Math.round(item.progress * 100)}%
                </span>
              </div>
              <Meter value={item.progress} className="mt-2" />
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Library() {
  const [documents, setDocuments] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(() => {
    api.listDocuments().then(setDocuments).catch(setError)
  }, [])

  useEffect(refresh, [refresh])

  const remove = async (id, name) => {
    if (!window.confirm(`Delete "${name}"? This also removes its index and analysis.`)) return
    try {
      await api.deleteDocument(id)
      refresh()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Document library</h1>
        <p className="mt-1 text-[--color-muted]">
          Upload climate policies, NDCs and adaptation plans. Each is segmented, embedded, classified
          against a nine-dimension policy taxonomy, and mined for quantified targets.
        </p>
      </div>

      <UploadZone onUploaded={refresh} />

      <ErrorNote error={error} />

      {documents === null ? (
        <Spinner label="Loading library" />
      ) : documents.length === 0 ? (
        <EmptyState icon={FileText} title="No documents yet">
          Upload two policies to unlock comparison, or one to start asking questions.
        </EmptyState>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {documents.map((doc) => (
            <Card key={doc.id} className="animate-fade-up flex flex-col p-4 transition hover:shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <Link
                  to={`/documents/${doc.id}`}
                  className="font-medium leading-snug hover:text-[--color-accent] hover:underline"
                >
                  {doc.name}
                </Link>
                <StatusBadge status={doc.status} />
              </div>

              {doc.error && <p className="mt-2 text-xs text-[--color-danger]">{doc.error}</p>}

              <dl className="tnum mt-3 grid grid-cols-3 gap-2 text-xs text-[--color-muted]">
                <div>
                  <dt>Pages</dt>
                  <dd className="text-sm text-[--color-ink]">{doc.page_count}</dd>
                </div>
                <div>
                  <dt>Words</dt>
                  <dd className="text-sm text-[--color-ink]">{doc.word_count.toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Passages</dt>
                  <dd className="text-sm text-[--color-ink]">{doc.chunk_count}</dd>
                </div>
              </dl>

              <div className="mt-4 flex items-center justify-between border-t border-[--color-line] pt-3">
                <Link to={`/documents/${doc.id}`} className="text-sm font-medium text-[--color-accent] hover:underline">
                  View analysis
                </Link>
                <Button variant="ghost" onClick={() => remove(doc.id, doc.name)} aria-label={`Delete ${doc.name}`}>
                  <Trash2 className="h-4 w-4" aria-hidden />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
