import React, { useMemo, useState } from 'react'

const defaultAPI = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const initialForm = {
  location: '',
  month: '',
  temperature_c: '',
  humidity_pct: '',
  wind_kmh: ''
}

export default function App() {
  const [form, setForm] = useState(initialForm)
  const [touched, setTouched] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [submitted, setSubmitted] = useState(false) // show results only after submit

  const apiBase = useMemo(
    () => (defaultAPI.endsWith('/') ? defaultAPI.slice(0, -1) : defaultAPI),
    []
  )

  // ---------- validation ----------
  const validate = (f) => {
    const e = {}
    if (!f.location?.trim()) e.location = 'Location is required'

    if (f.month === '' || f.month === null) e.month = 'Month is required'
    else if (isNaN(Number(f.month))) e.month = 'Month must be a number'
    else if (Number(f.month) < 1 || Number(f.month) > 12) e.month = 'Month must be 1–12'

    if (f.temperature_c === '' || f.temperature_c === null) e.temperature_c = 'Temperature is required'
    else if (isNaN(Number(f.temperature_c))) e.temperature_c = 'Temperature must be a number'
    else if (Number(f.temperature_c) < -50 || Number(f.temperature_c) > 60)
      e.temperature_c = 'Unrealistic temperature (-50 to 60 °C)'

    if (f.humidity_pct === '' || f.humidity_pct === null) e.humidity_pct = 'Humidity is required'
    else if (isNaN(Number(f.humidity_pct))) e.humidity_pct = 'Humidity must be a number'
    else if (Number(f.humidity_pct) < 0 || Number(f.humidity_pct) > 100)
      e.humidity_pct = 'Humidity must be 0–100'

    if (f.wind_kmh === '' || f.wind_kmh === null) e.wind_kmh = 'Wind speed is required'
    else if (isNaN(Number(f.wind_kmh))) e.wind_kmh = 'Wind must be a number'
    else if (Number(f.wind_kmh) < 0) e.wind_kmh = 'Wind must be ≥ 0'

    return e
  }
  const errors = validate(form)
  const isValid = Object.keys(errors).length === 0

  // ---------- helpers ----------
  const clamp = (val, min, max) => {
    let n = Number(val)
    if (isNaN(n)) return val
    if (min !== undefined && n < Number(min)) n = Number(min)
    if (max !== undefined && n > Number(max)) n = Number(max)
    return String(n)
  }
  const roundToStep = (val, step) => {
    if (!step) return val
    const n = Number(val)
    if (isNaN(n)) return val
    const s = Number(step)
    return String(Math.round(n / s) * s)
  }

  // ---------- handlers ----------
  const onChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const onBlur = (e) => {
    const { name, min, max, step, value } = e.target
    setTouched((prev) => ({ ...prev, [name]: true }))
    let v = value
    v = clamp(v, min, max)
    v = roundToStep(v, step)
    if (v !== value) {
      setForm((prev) => ({ ...prev, [name]: v }))
    }
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    setSubmitted(true)
    setTouched({
      location: true,
      month: true,
      temperature_c: true,
      humidity_pct: true,
      wind_kmh: true,
    })
    if (!isValid) return

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = {
        location: form.location.trim(),
        month: Number(form.month),
        temperature_c: Number(form.temperature_c),
        humidity_pct: Number(form.humidity_pct),
        wind_kmh: Number(form.wind_kmh),
      }
      const res = await fetch(`${apiBase}/api/recommendations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  const Field = ({ label, name, inputProps }) => (
    <label style={styles.label}>
      {label}
      <input
        style={{
          ...styles.input,
          ...(touched[name] && errors[name] ? styles.inputError : null),
        }}
        name={name}
        value={form[name]}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={label}
        {...inputProps}
      />
      {touched[name] && errors[name] && (
        <span style={styles.errText}>{errors[name]}</span>
      )}
    </label>
  )

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={{ marginTop: 0 }}>🌤️ Weather Recommendation</h1>
        <p style={{ opacity: 0.8, marginTop: -8 }}>
          Enter the conditions for a day and get a predicted weather label plus similar historical days.
        </p>

        <form onSubmit={onSubmit} style={styles.grid} noValidate>
          <Field label="Location" name="location" />
          <Field label="Month" name="month"
            inputProps={{ type: 'text', inputMode: 'numeric', pattern: '[0-9]*', min: 1, max: 12 }} />
          <Field label="Temperature (°C)" name="temperature_c"
            inputProps={{ type: 'text', inputMode: 'decimal', pattern: '[0-9]*[.,]?[0-9]*', step: 0.1 }} />
          <Field label="Humidity (%)" name="humidity_pct"
            inputProps={{ type: 'text', inputMode: 'numeric', pattern: '[0-9]*', min: 0, max: 100, step: 1 }} />
          <Field label="Wind (km/h)" name="wind_kmh"
            inputProps={{ type: 'text', inputMode: 'decimal', pattern: '[0-9]*[.,]?[0-9]*', min: 0, step: 0.1 }} />

          <div style={{ gridColumn: '1 / -1' }}>
            <button
              style={{ ...styles.button, opacity: isValid ? 1 : 0.7 }}
              disabled={loading || !isValid}
            >
              {loading ? 'Thinking…' : 'Get Recommendation'}
            </button>
          </div>
        </form>

        {error && <div style={styles.error}>⚠️ {error}</div>}

        {submitted && result && (
          <div style={styles.result}>
            <h2 style={{ marginTop: 0 }}>Result</h2>
            <p>
              <strong>Predicted:</strong> {result.predicted_condition}{' '}
              <span style={styles.badge}>
                {(result.confidence * 100).toFixed(1)}% confidence
              </span>
            </p>
            <h3>Top similar days</h3>
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th>Location</th>
                    <th>Month</th>
                    <th>Temp (°C)</th>
                    <th>Humidity (%)</th>
                    <th>Wind (km/h)</th>
                    <th>Condition</th>
                    <th>Similarity</th>
                  </tr>
                </thead>
                <tbody>
                  {result.top_similar_days.map((d, i) => (
                    <tr key={i}>
                      <td>{d.location}</td>
                      <td>{d.month}</td>
                      <td>{d.temperature_c.toFixed(1)}</td>
                      <td>{d.humidity_pct}</td>
                      <td>{d.wind_kmh.toFixed(1)}</td>
                      <td>{d.condition}</td>
                      <td>{(d.similarity * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p style={{ opacity: 0.7, fontSize: 14 }}>{result.message}</p>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #e0f2fe 0%, #f1f5f9 100%)',
    padding: 24,
  },
  card: {
    background: 'white',
    borderRadius: 16,
    padding: 24,
    width: 'min(920px, 95vw)',
    boxShadow: '0 10px 30px rgba(0,0,0,.08)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
    gap: 12,
    marginTop: 12,
  },
  label: { display: 'flex', flexDirection: 'column', fontWeight: 600 },
  input: {
    marginTop: 6,
    padding: '10px 12px',
    borderRadius: 10,
    border: '1px solid #e5e7eb',
    outline: 'none',
  },
  inputError: { borderColor: '#ef4444', background: '#fff7f7' },
  errText: { color: '#b91c1c', fontSize: 12, marginTop: 6, fontWeight: 500 },
  button: {
    width: '100%',
    padding: '12px 16px',
    borderRadius: 12,
    border: 'none',
    background: 'linear-gradient(135deg, #38bdf8, #22c55e)',
    color: 'white',
    fontWeight: 700,
    cursor: 'pointer',
  },
  error: {
    marginTop: 16,
    background: '#fee2e2',
    border: '1px solid #fecaca',
    padding: 12,
    borderRadius: 10,
  },
  result: {
    marginTop: 20,
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    padding: 16,
    borderRadius: 12,
  },
  tableWrap: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse' },
  badge: {
    background: '#eef2ff',
    padding: '4px 8px',
    borderRadius: 8,
    fontSize: 12,
    fontWeight: 700,
    marginLeft: 8,
  },
}
