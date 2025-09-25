import { useMemo, useState } from 'react'

function App() {
  const API_BASE = useMemo(
    () => import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000/api/v1',
    []
  )

  const [singleFile, setSingleFile] = useState(null)
  const [batchFiles, setBatchFiles] = useState([])

  const [isUploadingSingle, setIsUploadingSingle] = useState(false)
  const [isUploadingBatch, setIsUploadingBatch] = useState(false)

  const [singleResult, setSingleResult] = useState(null)
  const [batchResults, setBatchResults] = useState(null)
  const [error, setError] = useState(null)

  const resetStates = () => {
    setSingleResult(null)
    setBatchResults(null)
    setError(null)
  }

  const handleSingleUpload = async (e) => {
    e.preventDefault()
    resetStates()

    if (!singleFile) {
      setError('Please choose a PDF file to upload.')
      return
    }

    const formData = new FormData()
    formData.append('file', singleFile)

    setIsUploadingSingle(true)
    try {
      const res = await fetch(`${API_BASE}/documents/upload/`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        let msg = `Upload failed (${res.status})`
        try {
          const data = await res.json()
          msg += data?.detail ? `: ${data.detail}` : ''
        } catch {
          const txt = await res.text()
          msg += txt ? `: ${txt}` : ''
        }
        throw new Error(msg)
      }
      const data = await res.json()
      setSingleResult(data)
    } catch (err) {
      setError(err.message || 'Unexpected error during upload')
    } finally {
      setIsUploadingSingle(false)
    }
  }

  const handleBatchUpload = async (e) => {
    e.preventDefault()
    resetStates()

    if (!batchFiles || batchFiles.length === 0) {
      setError('Please choose one or more PDF files to upload.')
      return
    }

    const formData = new FormData()
    for (const f of batchFiles) {
      formData.append('files', f)
    }

    setIsUploadingBatch(true)
    try {
      const res = await fetch(`${API_BASE}/documents/upload/batch/`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        let msg = `Batch upload failed (${res.status})`
        try {
          const data = await res.json()
          msg += data?.detail ? `: ${data.detail}` : ''
        } catch {
          const txt = await res.text()
          msg += txt ? `: ${txt}` : ''
        }
        throw new Error(msg)
      }
      const data = await res.json()
      setBatchResults(data)
    } catch (err) {
      setError(err.message || 'Unexpected error during batch upload')
    } finally {
      setIsUploadingBatch(false)
    }
  }

  const DocumentCard = ({ doc }) => {
    if (!doc) return null
    const d = doc.document
    if (!d)
      return (
        <div className="p-4 rounded-lg border border-red-300 bg-red-50 text-red-700">
          No document details returned.
        </div>
      )

    return (
      <div className="p-4 rounded-lg border bg-white shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{d.metadata?.title || d.file_name}</h3>
          <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700">
            {d.file_type?.toUpperCase()}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-sm text-slate-700">
          <div>
            <span className="font-medium">Language:</span> {d.language || 'N/A'}
          </div>
          <div>
            <span className="font-medium">Size:</span> {Intl.NumberFormat().format(d.file_size)} bytes
          </div>
          <div>
            <span className="font-medium">Pages:</span> {d.metadata?.page_count ?? 'N/A'}
          </div>
          <div>
            <span className="font-medium">Processed:</span> {new Date(d.processing_date).toLocaleString()}
          </div>
        </div>
        {Array.isArray(d.keywords) && d.keywords.length > 0 && (
          <div className="text-sm">
            <div className="font-medium mb-1">Keywords</div>
            <div className="flex flex-wrap gap-2">
              {d.keywords.map((k, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"
                >
                  {k}
                </span>
              ))}
            </div>
          </div>
        )}
        {Array.isArray(d.sections) && d.sections.length > 0 && (
          <details className="text-sm">
            <summary className="cursor-pointer font-medium">Sections ({d.sections.length})</summary>
            <ul className="mt-2 space-y-1 list-disc list-inside">
              {d.sections.map((s, i) => (
                <li key={i}>
                  <span className="font-medium">{s.title}</span> — lines {s.start_line}-{s.end_line}
                </li>
              ))}
            </ul>
          </details>
        )}
        {d.text && (
          <details className="text-sm">
            <summary className="cursor-pointer font-medium">Extracted Text (preview)</summary>
            <pre className="whitespace-pre-wrap mt-2 max-h-64 overflow-auto bg-slate-50 p-3 rounded">
              {(d.text || '').slice(0, 500)}
              {(d.text || '').length > 500 ? '…' : ''}
            </pre>
          </details>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Climate Policy Analysis</h1>
          <p className="text-slate-600 text-sm">
            Upload PDF documents to process and extract metadata, sections, and keywords.
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        {error && (
          <div className="p-4 rounded border border-red-300 bg-red-50 text-red-700">{error}</div>
        )}

        <section className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Single PDF or DOC Upload</h2>
          <form onSubmit={handleSingleUpload} className="space-y-4">
            <div>
              <input
                type="file"
                accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
                onChange={(e) => setSingleFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={isUploadingSingle}
                className="inline-flex items-center justify-center rounded bg-emerald-600 px-4 py-2 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isUploadingSingle ? 'Uploading…' : 'Upload & Process'}
              </button>
              <div className="text-xs text-slate-500">Endpoint: {API_BASE}/documents/upload/</div>
            </div>
          </form>

          {singleResult && (
            <div className="mt-6">
              {singleResult.success ? (
                <DocumentCard doc={singleResult} />
              ) : (
                <div className="p-4 rounded border border-amber-300 bg-amber-50 text-amber-800">
                  {singleResult.message || 'Processing failed'}
                  {singleResult.error ? ` — ${singleResult.error}` : ''}
                </div>
              )}
            </div>
          )}
        </section>

        <section className="bg-white p-6 rounded-lg shadow-sm border">
          <h2 className="text-xl font-semibold mb-4">Batch PDF or DOC Upload</h2>
          <form onSubmit={handleBatchUpload} className="space-y-4">
            <div>
              <input
                type="file"
                accept="application/pdf,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.docx"
                multiple
                onChange={(e) => setBatchFiles(Array.from(e.target.files || []))}
                className="block w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={isUploadingBatch}
                className="inline-flex items-center justify-center rounded bg-blue-600 px-4 py-2 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isUploadingBatch ? 'Uploading…' : 'Upload Batch'}
              </button>
              <div className="text-xs text-slate-500">
                Endpoint: {API_BASE}/documents/upload/batch/
              </div>
            </div>
          </form>

          {Array.isArray(batchResults) && (
            <div className="mt-6 space-y-4">
              {batchResults.map((r, idx) => (
                <div
                  key={idx}
                  className={
                    'rounded border p-4 ' +
                    (r.success ? 'border-emerald-300 bg-emerald-50' : 'border-amber-300 bg-amber-50')
                  }
                >
                  <div className="font-medium mb-2">
                    {r.message || (r.success ? 'Processed' : 'Failed')}
                  </div>
                  {r.error && <div className="text-sm text-amber-800">{r.error}</div>}
                  {r.success && r.document && <DocumentCard doc={r} />}
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="text-xs text-slate-500">
          <div>
            Tip: Configure API base via <code>VITE_API_BASE_URL</code> (e.g., http://localhost:8000/api/v1).
          </div>
        </section>
      </main>

      <footer className="border-t bg-white">
        <div className="max-w-5xl mx-auto px-4 py-4 text-xs text-slate-500">
          © {new Date().getFullYear()} Climate Policy Analysis
        </div>
      </footer>
    </div>
  )
}

export default App