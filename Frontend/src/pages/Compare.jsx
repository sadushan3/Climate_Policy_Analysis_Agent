import { useEffect, useState } from 'react'
import { ArrowLeftRight, GitCompareArrows, Sparkles } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api, followJob } from '../lib/api'
import { Badge, Button, Card, EmptyState, ErrorNote, SectionTitle, Spinner, Stat } from '../components/ui'

const VERDICT_TONE = {
  only_a: 'accent',
  only_b: 'accent',
  stronger_a: 'warn',
  stronger_b: 'warn',
  equivalent: 'neutral',
  comparable: 'neutral',
  both: 'neutral',
}

/** Renders a verdict with the documents' real names instead of "A"/"B". */
function verdictText(verdict, nameA, nameB) {
  return {
    only_a: `Only ${nameA}`,
    only_b: `Only ${nameB}`,
    stronger_a: `${nameA} stronger`,
    stronger_b: `${nameB} stronger`,
    equivalent: 'Equivalent',
    comparable: 'Comparable',
    both: 'Both',
  }[verdict] ?? verdict
}

function DocumentPicker({ label, documents, value, onChange, exclude }) {
  return (
    <label className="flex-1">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-[--color-muted]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-[--color-line] bg-[--color-surface] px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-[--color-accent]"
      >
        <option value="">Select a document…</option>
        {documents
          .filter((d) => d.status === 'ready' && d.id !== exclude)
          .map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
      </select>
    </label>
  )
}

function DimensionChart({ rows, nameA, nameB }) {
  const data = rows
    .filter((r) => r.share_a > 0 || r.share_b > 0)
    .map((r) => ({
      dimension: r.label.split(' & ')[0].split(', ')[0],
      [nameA]: Number((r.share_a * 100).toFixed(1)),
      [nameB]: Number((r.share_b * 100).toFixed(1)),
    }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(240, data.length * 38)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid horizontal={false} stroke="var(--color-line)" />
        <XAxis type="number" unit="%" tick={{ fontSize: 11, fill: 'var(--color-muted)' }} />
        <YAxis
          type="category"
          dataKey="dimension"
          width={110}
          tick={{ fontSize: 11, fill: 'var(--color-muted)' }}
        />
        <Tooltip
          formatter={(value) => `${value}%`}
          contentStyle={{ borderRadius: 8, border: '1px solid var(--color-line)', fontSize: 12 }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey={nameA} fill="var(--color-accent)" radius={[0, 3, 3, 0]} />
        <Bar dataKey={nameB} fill="#8aa8b8" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function Compare() {
  const [documents, setDocuments] = useState([])
  const [docA, setDocA] = useState('')
  const [docB, setDocB] = useState('')
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listDocuments().then(setDocuments).catch(setError)
  }, [])

  const run = async () => {
    setError(null)
    setResult(null)
    setProgress({ stage: 'queued', progress: 0 })
    try {
      const { job_id } = await api.compare(docA, docB)
      const payload = await followJob(job_id, { onProgress: setProgress })
      setResult(payload)
    } catch (err) {
      setError(err)
    } finally {
      setProgress(null)
    }
  }

  const ready = documents.filter((d) => d.status === 'ready')
  const nameA = result?.documents.a.name ?? 'A'
  const nameB = result?.documents.b.name ?? 'B'

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Compare policies</h1>
        <p className="mt-1 text-[--color-muted]">
          Passage-level semantic alignment, dimension coverage and a target-by-target ambition diff.
        </p>
      </div>

      {ready.length < 2 ? (
        <EmptyState icon={GitCompareArrows} title="Two analysed documents are needed">
          You have {ready.length}. Upload another in the Library.
        </EmptyState>
      ) : (
        <Card className="flex flex-col items-end gap-4 p-5 sm:flex-row">
          <DocumentPicker label="Document A" documents={documents} value={docA} onChange={setDocA} exclude={docB} />
          <ArrowLeftRight className="mb-2 hidden h-4 w-4 shrink-0 text-[--color-muted] sm:block" aria-hidden />
          <DocumentPicker label="Document B" documents={documents} value={docB} onChange={setDocB} exclude={docA} />
          <Button onClick={run} disabled={!docA || !docB || !!progress} className="w-full sm:w-auto">
            {progress ? 'Comparing…' : 'Compare'}
          </Button>
        </Card>
      )}

      <ErrorNote error={error} />

      {progress && (
        <Card className="p-5">
          <Spinner label={`${progress.stage} · ${Math.round((progress.progress ?? 0) * 100)}%`} />
        </Card>
      )}

      {result && (
        <div className="animate-fade-up space-y-8">
          <Card className="grid grid-cols-2 gap-6 p-5 sm:grid-cols-4">
            <Stat
              label="Overall similarity"
              value={result.similarity.overall.toFixed(2)}
              hint="symmetric best-match mean"
            />
            <Stat
              label={`${nameA} covered`}
              value={`${Math.round(result.similarity.coverage_a * 100)}%`}
              hint={`has a counterpart in ${nameB}`}
            />
            <Stat
              label={`${nameB} covered`}
              value={`${Math.round(result.similarity.coverage_b * 100)}%`}
              hint={`has a counterpart in ${nameA}`}
            />
            <Stat label="Aligned pairs" value={result.similarity.aligned_pair_count} hint="one-to-one matches" />
          </Card>

          {result.narrative ? (
            <section>
              <SectionTitle hint="grounded in the computed results below">Analyst read</SectionTitle>
              <Card className="p-5">
                <Badge tone="accent" className="mb-3">
                  <Sparkles className="h-3 w-3" aria-hidden /> AI-written
                </Badge>
                <div className="space-y-3 leading-relaxed">
                  {result.narrative.split('\n').filter(Boolean).map((line, i) =>
                    line.startsWith('## ') ? (
                      <h3 key={i} className="pt-2 text-sm font-semibold uppercase tracking-wide text-[--color-muted]">
                        {line.slice(3)}
                      </h3>
                    ) : (
                      <p key={i}>{line}</p>
                    ),
                  )}
                </div>
              </Card>
            </section>
          ) : (
            <Card className="p-4 text-sm text-[--color-muted]">
              Written synthesis is off. Set <code className="rounded bg-[--color-canvas] px-1">ANTHROPIC_API_KEY</code>{' '}
              to enable it — every number below is computed locally and unaffected.
            </Card>
          )}

          <section>
            <SectionTitle hint="share of each document">Coverage by dimension</SectionTitle>
            <Card className="p-4">
              <DimensionChart rows={result.dimensions} nameA={nameA} nameB={nameB} />
            </Card>
          </section>

          <section>
            <SectionTitle>Target-by-target ambition</SectionTitle>
            {result.targets.length === 0 ? (
              <EmptyState title="No quantified targets in either document" />
            ) : (
              <Card className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[--color-line] text-left text-xs uppercase tracking-wide text-[--color-muted]">
                      <th className="px-4 py-2.5 font-medium">Target</th>
                      <th className="px-4 py-2.5 font-medium">{nameA}</th>
                      <th className="px-4 py-2.5 font-medium">{nameB}</th>
                      <th className="px-4 py-2.5 font-medium">Verdict</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[--color-line]">
                    {result.targets.map((row) => (
                      <tr key={row.target_type}>
                        <td className="px-4 py-3 font-medium">{row.target_type.replace(/_/g, ' ')}</td>
                        <td className="tnum px-4 py-3">
                          {row.a ? `${row.a.value ?? ''}${row.a.unit ?? ''} by ${row.a.target_year ?? '—'}` : '—'}
                        </td>
                        <td className="tnum px-4 py-3">
                          {row.b ? `${row.b.value ?? ''}${row.b.unit ?? ''} by ${row.b.target_year ?? '—'}` : '—'}
                        </td>
                        <td className="px-4 py-3">
                          <Badge tone={VERDICT_TONE[row.verdict]}>{verdictText(row.verdict, nameA, nameB)}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            )}
          </section>

          <section>
            <SectionTitle hint="highest-similarity one-to-one matches">Shared commitments</SectionTitle>
            <div className="space-y-3">
              {result.alignment.pairs.slice(0, 8).map((pair, i) => (
                <Card key={i} className="p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Badge tone={pair.relation === 'equivalent' ? 'accent' : 'neutral'}>{pair.relation}</Badge>
                    <span className="tnum text-xs text-[--color-muted]">{pair.similarity.toFixed(2)}</span>
                  </div>
                  <div className="grid gap-3 text-sm sm:grid-cols-2">
                    <div>
                      <div className="mb-1 text-xs font-medium text-[--color-muted]">
                        {nameA} · p.{pair.left.page}
                      </div>
                      <p className="leading-relaxed">{pair.left.text}</p>
                    </div>
                    <div className="sm:border-l sm:border-[--color-line] sm:pl-3">
                      <div className="mb-1 text-xs font-medium text-[--color-muted]">
                        {nameB} · p.{pair.right.page}
                      </div>
                      <p className="leading-relaxed">{pair.right.text}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            {[
              { title: `Only in ${nameA}`, items: result.unique_to_a },
              { title: `Only in ${nameB}`, items: result.unique_to_b },
            ].map(({ title, items }) => (
              <div key={title}>
                <SectionTitle hint={`${items.length} passages`}>{title}</SectionTitle>
                <Card className="divide-y divide-[--color-line]">
                  {items.length === 0 ? (
                    <p className="px-4 py-6 text-sm text-[--color-muted]">
                      Every passage has a counterpart in the other document.
                    </p>
                  ) : (
                    items.slice(0, 6).map((item) => (
                      <div key={item.chunk_index} className="px-4 py-3 text-sm">
                        <span className="tnum mr-2 text-xs text-[--color-muted]">p.{item.page}</span>
                        {item.text}
                      </div>
                    ))
                  )}
                </Card>
              </div>
            ))}
          </section>
        </div>
      )}
    </div>
  )
}
