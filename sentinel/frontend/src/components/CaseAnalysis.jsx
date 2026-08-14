import { useState } from 'react'
import { C } from '../tokens'

const BACKEND = 'http://localhost:8000'

const LBL = {
  fontSize: '0.52rem', textTransform: 'uppercase',
  letterSpacing: '0.14em', color: C.muted,
  marginBottom: '0.4rem',
}
const MONO = { fontFamily: 'monospace' }

const VERDICT_COLOR = {
  'HIGH':                  C.green,
  'MEDIUM':                C.yellow,
  'LOW / REVIEW REQUIRED': C.red,
}

function Panel({ children, style }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 6, ...style,
    }}>
      {children}
    </div>
  )
}

function TrustBadge({ score, verdict }) {
  const color = VERDICT_COLOR[verdict] || C.muted
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <span style={{
        fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em',
        color, background: color + '20', border: `1px solid ${color + '50'}`,
        borderRadius: 999, padding: '0.25rem 0.9rem',
      }}>
        {verdict}
      </span>
      <span style={{ ...MONO, fontSize: '0.75rem', color: C.muted }}>
        Trust score: <span style={{ color, fontWeight: 700 }}>{(score * 100).toFixed(1)}%</span>
      </span>
    </div>
  )
}

function ClaimTable({ claims }) {
  if (!claims || claims.length === 0) return null
  const th = {
    ...MONO, fontSize: '0.58rem', textTransform: 'uppercase', letterSpacing: '0.1em',
    color: C.dim, padding: '0.4rem 0.75rem', borderBottom: `1px solid ${C.border}`,
    textAlign: 'left', fontWeight: 600,
  }
  const td = {
    ...MONO, fontSize: '0.72rem', color: C.muted,
    padding: '0.45rem 0.75rem', verticalAlign: 'top',
    borderBottom: `1px solid ${C.border}`,
  }
  return (
    <div>
      <p style={LBL}>Claims</p>
      <Panel style={{ overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={th}>Claim</th>
              <th style={{ ...th, width: 60, textAlign: 'center' }}>Page</th>
              <th style={{ ...th, width: 50, textAlign: 'center' }}>OK?</th>
            </tr>
          </thead>
          <tbody>
            {claims.map((c, i) => (
              <tr key={i}>
                <td style={{ ...td, lineHeight: 1.55 }}>{c.text}</td>
                <td style={{ ...td, textAlign: 'center', color: C.blue }}>{c.cited_page ?? '—'}</td>
                <td style={{
                  ...td, textAlign: 'center',
                  color: c.verified === true ? C.green : c.verified === false ? C.red : C.dim,
                }}>
                  {c.verified === true ? '✓' : c.verified === false ? '✗' : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  )
}

function ContradictionsPanel({ contradictions }) {
  if (!contradictions || contradictions.length === 0) return null
  return (
    <div>
      <p style={{ ...LBL, color: C.red }}>⚠ Contradictions detected ({contradictions.length})</p>
      <Panel style={{ overflow: 'hidden' }}>
        {contradictions.map((c, i) => (
          <div key={i} style={{
            padding: '0.65rem 0.9rem',
            borderBottom: i < contradictions.length - 1 ? `1px solid ${C.border}` : 'none',
          }}>
            <span style={{ ...MONO, fontSize: '0.65rem', textTransform: 'uppercase', color: C.red, letterSpacing: '0.1em', marginRight: '0.6rem' }}>
              {c.label}
            </span>
            <span style={{ ...MONO, fontSize: '0.72rem', color: C.muted }}>
              Page {c.page_a}: <span style={{ color: C.yellow }}>"{c.value_a}"</span>
              {' '}vs Page {c.page_b}: <span style={{ color: C.red }}>"{c.value_b}"</span>
            </span>
          </div>
        ))}
      </Panel>
    </div>
  )
}

function ResponsePanel({ response }) {
  if (!response) return null
  if (response.status === 'INJECTION_DETECTED') {
    return (
      <Panel style={{ padding: '1rem 1.25rem', borderColor: C.redBrd }}>
        <p style={{ ...LBL, color: C.red }}>Query rejected</p>
        <p style={{ ...MONO, fontSize: '0.8rem', color: C.red }}>
          Prompt injection detected. Query was not processed.
        </p>
      </Panel>
    )
  }
  if (response.status === 'ERROR') {
    return (
      <Panel style={{ padding: '1rem 1.25rem', borderColor: C.redBrd }}>
        <p style={{ ...LBL, color: C.red }}>Error</p>
        <pre style={{ ...MONO, fontSize: '0.75rem', color: C.red, whiteSpace: 'pre-wrap' }}>
          {response.message}
        </pre>
      </Panel>
    )
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {response.trust_score != null && (
        <Panel style={{ padding: '0.85rem 1.1rem' }}>
          <p style={LBL}>Trust Assessment</p>
          <TrustBadge score={response.trust_score} verdict={response.verdict} />
        </Panel>
      )}
      {response.answer && (
        <Panel style={{ padding: '0.85rem 1.1rem' }}>
          <p style={LBL}>Answer</p>
          <p style={{ fontSize: '0.875rem', color: C.text, lineHeight: 1.65 }}>{response.answer}</p>
        </Panel>
      )}
      {response.contradictions && response.contradictions.length > 0 && (
        <ContradictionsPanel contradictions={response.contradictions} />
      )}
      {response.claims && response.claims.length > 0 && (
        <ClaimTable claims={response.claims} />
      )}

      {/* Raw JSON toggle */}
      <RawToggle data={response} />
    </div>
  )
}

function RawToggle({ data }) {
  const [open, setOpen] = useState(false)
  return (
    <Panel style={{ overflow: 'hidden' }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          padding: '0.5rem 0.9rem', display: 'flex', justifyContent: 'space-between',
          alignItems: 'center', cursor: 'pointer', userSelect: 'none',
        }}
      >
        <span style={{ fontSize: '0.58rem', textTransform: 'uppercase', letterSpacing: '0.12em', color: C.dim }}>
          Raw JSON — POST /api/query
        </span>
        <span style={{ ...MONO, fontSize: '0.65rem', color: C.dim }}>
          {open ? '▲ hide' : '▼ show'}
        </span>
      </div>
      {open && (
        <pre style={{
          ...MONO, padding: '0.9rem', fontSize: '0.7rem', color: C.muted,
          borderTop: `1px solid ${C.border}`, overflowX: 'auto',
          maxHeight: 420, overflowY: 'auto', margin: 0,
        }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </Panel>
  )
}

export default function CaseAnalysis({ conn }) {
  const [question, setQuestion] = useState('')
  const [caseFile, setCaseFile] = useState('millbrook_arson_2019')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState(null)

  const submit = async () => {
    if (!question.trim() || loading) return
    setLoading(true); setResponse(null)
    try {
      const res = await fetch(`${BACKEND}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), case_file: caseFile }),
      })
      setResponse(await res.json())
    } catch (err) {
      setResponse({ status: 'ERROR', message: String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', padding: '2.5rem 1.5rem',
    }}>
      <div style={{ width: '100%', maxWidth: 700 }}>

        {/* Hero */}
        <p style={{
          fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.18em',
          color: C.cyan, marginBottom: '1rem',
        }}>
          RAG + Trust Layer · v1.0
        </p>
        <h1 style={{
          fontSize: '2rem', fontWeight: 800, color: C.white,
          lineHeight: 1.2, marginBottom: '0.6rem', letterSpacing: '-0.02em',
        }}>
          Every cold case.<br />
          Every piece of evidence.<br />
          <span style={{ color: C.cyan }}>Trusted.</span>
        </h1>
        <p style={{ fontSize: '0.875rem', color: C.muted, marginBottom: '2rem', lineHeight: 1.65 }}>
          Evidence Retrieval with Trust Layer. Every answer is scored, every claim is verified,
          every contradiction is flagged.
        </p>

        {/* Connection status */}
        <div style={{
          ...Panel,
          background: C.surface, border: `1px solid ${C.border}`,
          borderRadius: 6, padding: '0.65rem 1rem', marginBottom: '1.25rem',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: conn === 'connected' ? C.green : conn === 'checking' ? C.yellow : C.red,
            boxShadow: `0 0 6px ${conn === 'connected' ? C.green : C.red}`,
          }} />
          <span style={{ fontSize: '0.75rem', color: C.muted }}>
            {conn === 'connected' ? 'Backend connected' : conn === 'checking' ? 'Connecting…' : 'Backend offline'}
          </span>
        </div>

        {/* Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '1.25rem' }}>
          <div>
            <p style={LBL}>Case File</p>
            <select
              value={caseFile}
              onChange={e => setCaseFile(e.target.value)}
              style={{
                width: '100%', background: C.surface, border: `1px solid ${C.borderHi}`,
                borderRadius: 6, padding: '0.6rem 1rem', color: C.text,
                fontSize: '0.875rem', outline: 'none', cursor: 'pointer',
              }}
            >
              <option value="millbrook_arson_2019">Millbrook Arson 2019 (authentic)</option>
              <option value="millbrook_arson_corrupted">Millbrook Arson 2019 (corrupted)</option>
            </select>
          </div>
          <div>
            <p style={LBL}>Investigation Question</p>
            <textarea
              style={{
                width: '100%', background: C.surface, border: `1px solid ${C.borderHi}`,
                borderRadius: 6, padding: '0.7rem 1rem', color: C.text,
                fontSize: '0.9rem', outline: 'none', resize: 'vertical',
                minHeight: 80, fontFamily: 'inherit', lineHeight: 1.5,
              }}
              placeholder="What accelerant was used in the Millbrook Arson?"
              value={question}
              onChange={e => setQuestion(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={submit}
              disabled={!question.trim() || loading}
              style={{
                background: (!question.trim() || loading) ? C.border : C.btn,
                color: (!question.trim() || loading) ? C.muted : C.white,
                border: 'none', borderRadius: 6, padding: '0.55rem 1.4rem',
                fontSize: '0.875rem', fontWeight: 600,
                cursor: (!question.trim() || loading) ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {loading ? 'Querying…' : 'Submit'}
            </button>
          </div>
        </div>

        <ResponsePanel response={response} />

      </div>
    </main>
  )
}
