import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

import { api } from '../lib/api'
import { Badge, Card, Citation, EmptyState, ErrorNote, Meter, SectionTitle, Spinner, Stat } from '../components/ui'

const TARGET_LABELS = {
  emissions_reduction: 'Emissions reduction',
  net_zero: 'Net zero',
  renewable_share: 'Renewable share',
  finance: 'Finance',
  energy_efficiency: 'Energy efficiency',
  sectoral: 'Sectoral',
  other: 'Other',
}

function formatValue(target) {
  if (target.value == null) return '—'
  if (target.unit === 'USD' || target.unit === 'EUR' || target.unit === 'GBP' || target.unit === 'LKR') {
    const millions = target.value / 1e6
    const text = millions >= 1000 ? `${(millions / 1000).toFixed(1)}bn` : `${millions.toFixed(0)}m`
    return `${target.unit} ${text}`
  }
  return `${target.value}${target.unit ?? ''}`
}

function CoverageRadar({ profile }) {
  const data = Object.entries(profile).map(([key, value]) => ({
    key,
    // Recharts renders the raw label; shorten the long ones so the axis stays legible.
    dimension: value.label.replace(' & ', ' / ').split(' / ')[0],
    score: Number((value.score * 100).toFixed(1)),
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="var(--color-line)" />
        <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: 'var(--color-muted)' }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        <Tooltip
          formatter={(value) => [`${value}`, 'Confidence']}
          contentStyle={{
            borderRadius: 8,
            border: '1px solid var(--color-line)',
            fontSize: 12,
          }}
        />
        <Radar
          dataKey="score"
          stroke="var(--color-accent)"
          fill="var(--color-accent)"
          fillOpacity={0.18}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

export default function DocumentDetail() {
  const { id } = useParams()
  const [doc, setDoc] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setDoc(null)
    api.getDocument(id).then(setDoc).catch(setError)
  }, [id])

  if (error) return <ErrorNote error={error} />
  if (!doc) return <Spinner label="Loading analysis" />

  const analysis = doc.analysis
  if (!analysis) {
    return (
      <EmptyState title={`"${doc.name}" has no analysis`}>
        Status is “{doc.status}”. {doc.error ?? 'Re-upload the document to analyse it.'}
      </EmptyState>
    )
  }

  const stats = analysis.statistics
  const presentDimensions = Object.entries(analysis.coverage_profile)
    .filter(([, v]) => v.present)
    .sort((a, b) => b[1].share - a[1].share)
  const missingDimensions = Object.entries(analysis.coverage_profile).filter(([, v]) => !v.present)

  return (
    <div className="space-y-8">
      <div>
        <Link to="/library" className="inline-flex items-center gap-1 text-sm text-[--color-muted] hover:text-[--color-ink]">
          <ArrowLeft className="h-4 w-4" aria-hidden /> Library
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">{doc.name}</h1>
        <p className="mt-1 text-sm text-[--color-muted]">
          {doc.original_name} · extracted with {doc.extractor}
        </p>
      </div>

      <Card className="grid grid-cols-2 gap-6 p-5 sm:grid-cols-5">
        <Stat label="Pages" value={stats.page_count} />
        <Stat label="Words" value={stats.word_count.toLocaleString()} />
        <Stat label="Passages" value={stats.chunk_count} />
        <Stat
          label="Targets"
          value={stats.target_count}
          hint={stats.conditional_target_count > 0 ? `${stats.conditional_target_count} conditional` : undefined}
        />
        <Stat
          label="Coverage"
          value={`${stats.dimensions_covered}/${stats.dimensions_total}`}
          hint="policy dimensions"
        />
      </Card>

      <section>
        <SectionTitle hint={analysis.summary_method === 'abstractive' ? 'Claude synthesis' : 'extractive (no API key)'}>
          Summary
        </SectionTitle>
        <Card className="p-5">
          {analysis.summary_method === 'abstractive' && (
            <Badge tone="accent" className="mb-3">
              <Sparkles className="h-3 w-3" aria-hidden /> AI-written
            </Badge>
          )}
          <p className="whitespace-pre-wrap leading-relaxed">{analysis.summary}</p>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div>
          <SectionTitle hint="max confidence per dimension">Policy coverage</SectionTitle>
          <Card className="p-4">
            <CoverageRadar profile={analysis.coverage_profile} />
            {missingDimensions.length > 0 && (
              <p className="mt-2 border-t border-[--color-line] pt-3 text-xs text-[--color-muted]">
                <span className="font-medium text-[--color-warn]">Not addressed:</span>{' '}
                {missingDimensions.map(([, v]) => v.label).join(', ')}
              </p>
            )}
          </Card>
        </div>

        <div>
          <SectionTitle hint="share of document">Dimension weight</SectionTitle>
          <Card className="divide-y divide-[--color-line]">
            {presentDimensions.map(([key, value]) => (
              <div key={key} className="px-4 py-3">
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-medium">{value.label}</span>
                  <span className="tnum text-xs text-[--color-muted]">
                    {(value.share * 100).toFixed(0)}% · conf {value.score.toFixed(2)}
                  </span>
                </div>
                <Meter value={value.share} className="mt-2" />
              </div>
            ))}
          </Card>
        </div>
      </section>

      <section>
        <SectionTitle hint={`${analysis.targets.length} extracted`}>Quantified commitments</SectionTitle>
        {analysis.targets.length === 0 ? (
          <EmptyState title="No quantified targets found">
            This document may be qualitative, or its targets are phrased in a way the extractor does not
            yet cover.
          </EmptyState>
        ) : (
          <Card className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[--color-line] text-left text-xs uppercase tracking-wide text-[--color-muted]">
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Value</th>
                  <th className="px-4 py-2.5 font-medium">By</th>
                  <th className="px-4 py-2.5 font-medium">Base</th>
                  <th className="px-4 py-2.5 font-medium">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[--color-line]">
                {analysis.targets.map((target, i) => (
                  <tr key={i} className="align-top">
                    <td className="px-4 py-3">
                      <div className="font-medium">{TARGET_LABELS[target.target_type] ?? target.target_type}</div>
                      {target.conditional && (
                        <Badge tone="warn" className="mt-1">
                          conditional
                        </Badge>
                      )}
                    </td>
                    <td className="tnum px-4 py-3 font-medium">{formatValue(target)}</td>
                    <td className="tnum px-4 py-3">{target.target_year ?? '—'}</td>
                    <td className="tnum px-4 py-3 text-[--color-muted]">{target.base_year ?? '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-start gap-2">
                        <Citation page={target.page} section={target.section} />
                        <span className="text-xs leading-relaxed text-[--color-muted]">{target.source_text}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </section>

      <section>
        <SectionTitle hint="the sentence that triggered each classification">Evidence</SectionTitle>
        <div className="grid gap-4 lg:grid-cols-2">
          {analysis.dimensions.map((dimension) => (
            <Card key={dimension.key} className="p-4">
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="font-medium">{dimension.label}</h3>
                <span className="tnum text-xs text-[--color-muted]">
                  {dimension.chunk_count} passages · {dimension.score.toFixed(2)}
                </span>
              </div>
              <ul className="mt-3 space-y-2.5">
                {dimension.evidence.map((item, i) => (
                  <li key={i} className="flex gap-2 text-sm leading-relaxed">
                    <Citation page={item.page_start} section={item.section} />
                    <span>{item.text}</span>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
