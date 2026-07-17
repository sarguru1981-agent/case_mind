import { useState, useEffect } from 'react'

const BACKEND = 'http://localhost:8000'

const S = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    background: '#0d1117',
    color: '#c9d1d9',
  },
  header: {
    borderBottom: '1px solid #21262d',
    padding: '1rem 2rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    fontSize: '1.1rem',
    fontWeight: 700,
    letterSpacing: '-0.02em',
  },
  badge: {
    fontSize: '0.62rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.1em',
    background: '#1c2d3e',
    color: '#58a6ff',
    border: '1px solid #1f4d7e',
    padding: '0.2rem 0.7rem',
    borderRadius: 999,
  },
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '4rem 2rem',
  },
  hero: {
    width: '100%',
    maxWidth: 640,
  },
  eyebrow: {
    fontSize: '0.62rem',
    textTransform: 'uppercase',
    letterSpacing: '0.18em',
    color: '#58a6ff',
    marginBottom: '1.25rem',
  },
  h1: {
    fontSize: '2.4rem',
    fontWeight: 800,
    color: '#fff',
    lineHeight: 1.2,
    marginBottom: '0.75rem',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: '0.875rem',
    color: '#8b949e',
    marginBottom: '2.5rem',
    lineHeight: 1.65,
  },
  card: {
    background: '#161b22',
    border: '1px solid #21262d',
    borderRadius: 8,
    padding: '1rem 1.25rem',
    marginBottom: '1.5rem',
  },
  cardLabel: {
    fontSize: '0.55rem',
    textTransform: 'uppercase',
    letterSpacing: '0.15em',
    color: '#484f58',
    marginBottom: '0.6rem',
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.6rem',
  },
  dot: color => ({
    width: 8,
    height: 8,
    borderRadius: '50%',
    background: color,
    flexShrink: 0,
  }),
  connText: color => ({
    fontSize: '0.875rem',
    fontWeight: 600,
    color,
  }),
  pre: {
    marginTop: '0.75rem',
    fontSize: '0.7rem',
    color: '#6e7681',
    fontFamily: 'monospace',
    lineHeight: 1.65,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  hint: {
    marginTop: '0.5rem',
    fontSize: '0.68rem',
    color: '#6e7681',
    fontFamily: 'monospace',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    marginBottom: '1.5rem',
  },
  sectionLabel: {
    fontSize: '0.6rem',
    textTransform: 'uppercase',
    letterSpacing: '0.14em',
    color: '#484f58',
    marginBottom: '0.4rem',
  },
  textarea: {
    width: '100%',
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: 6,
    padding: '0.7rem 1rem',
    color: '#c9d1d9',
    fontSize: '0.9rem',
    outline: 'none',
    resize: 'vertical',
    minHeight: 80,
    fontFamily: 'inherit',
    lineHeight: 1.5,
  },
  btnRow: {
    display: 'flex',
    justifyContent: 'flex-end',
  },
  btn: (disabled) => ({
    background: disabled ? '#21262d' : '#1f6feb',
    color: disabled ? '#484f58' : '#fff',
    border: 'none',
    borderRadius: 6,
    padding: '0.55rem 1.4rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
  }),
  responseCard: {
    background: '#161b22',
    border: '1px solid #21262d',
    borderRadius: 8,
    overflow: 'hidden',
  },
  responseHeader: {
    padding: '0.55rem 1rem',
    borderBottom: '1px solid #21262d',
    fontSize: '0.58rem',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    color: '#484f58',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  responsePre: {
    padding: '1rem',
    fontSize: '0.78rem',
    color: '#8b949e',
    fontFamily: 'monospace',
    lineHeight: 1.7,
    overflowX: 'auto',
    margin: 0,
  },
  footer: {
    borderTop: '1px solid #21262d',
    padding: '0.9rem',
    textAlign: 'center',
    fontSize: '0.62rem',
    color: '#484f58',
  },
}

const CONN_META = {
  checking:     { label: 'Checking backend…',    color: '#e3b341', dot: '#e3b341' },
  connected:    { label: 'Backend connected',     color: '#3fb950', dot: '#3fb950' },
  disconnected: { label: 'Backend not connected', color: '#f85149', dot: '#f85149' },
}

export default function App() {
  const [conn, setConn]           = useState('checking')
  const [versionData, setVersion] = useState(null)
  const [question, setQuestion]   = useState('')
  const [loading, setLoading]     = useState(false)
  const [response, setResponse]   = useState(null)
  const [statusCode, setStatus]   = useState(null)

  useEffect(() => {
    fetch(`${BACKEND}/version`)
      .then(r => r.json())
      .then(data => { setVersion(data); setConn('connected') })
      .catch(() => setConn('disconnected'))
  }, [])

  const handleSubmit = async () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setResponse(null)
    setStatus(null)
    try {
      const res = await fetch(`${BACKEND}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim() }),
      })
      setStatus(res.status)
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setResponse({ error: 'Failed to reach backend', detail: String(err) })
    } finally {
      setLoading(false)
    }
  }

  const meta = CONN_META[conn]

  return (
    <div style={S.app}>

      {/* ── Header ── */}
      <header style={S.header}>
        <div style={S.logo}>
          <span style={{ color: '#fff' }}>Case</span>
          <span style={{ color: '#1f6feb' }}>Mind</span>
          <span style={{ color: '#8b949e', fontWeight: 400, marginLeft: '0.4rem', fontSize: '0.95rem' }}>
            Sentinel
          </span>
        </div>
        <span style={S.badge}>Milestone 1 · v1.0</span>
      </header>

      {/* ── Main ── */}
      <main style={S.main}>
        <div style={S.hero}>

          <p style={S.eyebrow}>Police AI Investigation Platform</p>

          <h1 style={S.h1}>
            Every cold case.<br />
            Every piece of evidence.<br />
            <span style={{ color: '#58a6ff' }}>Trusted.</span>
          </h1>

          <p style={S.subtitle}>
            Milestone 1 — Foundation. Backend communication established.
            Evidence Retrieval Service and Trust Layer ship in Milestones 2–9.
          </p>

          {/* Connection status */}
          <div style={S.card}>
            <div style={S.cardLabel}>System Status</div>
            <div style={S.row}>
              <span style={S.dot(meta.dot)} />
              <span style={S.connText(meta.color)}>{meta.label}</span>
            </div>
            {versionData && (
              <pre style={S.pre}>{JSON.stringify(versionData, null, 2)}</pre>
            )}
            {conn === 'disconnected' && (
              <p style={S.hint}>
                cd sentinel/backend && uvicorn main:app --reload --port 8000
              </p>
            )}
          </div>

          {/* Query form */}
          <div style={S.form}>
            <div>
              <p style={S.sectionLabel}>Investigation Question</p>
              <textarea
                style={S.textarea}
                placeholder="Enter a detective investigation question…"
                value={question}
                onChange={e => setQuestion(e.target.value)}
              />
            </div>
            <div style={S.btnRow}>
              <button
                style={S.btn(!question.trim() || loading)}
                onClick={handleSubmit}
                disabled={!question.trim() || loading}
              >
                {loading ? 'Querying…' : 'Submit'}
              </button>
            </div>
          </div>

          {/* Response panel */}
          {response && (
            <div style={S.responseCard}>
              <div style={S.responseHeader}>
                <span>Response — POST /api/query</span>
                {statusCode && (
                  <span style={{ color: statusCode === 200 ? '#3fb950' : '#f85149' }}>
                    HTTP {statusCode}
                  </span>
                )}
              </div>
              <pre style={S.responsePre}>{JSON.stringify(response, null, 2)}</pre>
            </div>
          )}

        </div>
      </main>

      {/* ── Footer ── */}
      <footer style={S.footer}>
        CaseMind Sentinel v1.0 · Police AI Investigation Platform · The Detective's Guide to AI
      </footer>

    </div>
  )
}
