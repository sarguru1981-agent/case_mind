import { useState, useEffect } from 'react'
import Header from './components/Header'
import InvestigationConsole from './components/InvestigationConsole'
import CaseAnalysis from './components/CaseAnalysis'
import { C } from './tokens'

const BACKEND = 'http://localhost:8000'

export default function App() {
  const [tab, setTab]             = useState('investigation')
  const [conn, setConn]           = useState('checking')
  const [versionData, setVersion] = useState(null)

  useEffect(() => {
    fetch(`${BACKEND}/version`)
      .then(r => r.json())
      .then(d => { setVersion(d); setConn('connected') })
      .catch(() => setConn('disconnected'))
  }, [])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: C.bg }}>
      <Header tab={tab} onTab={setTab} conn={conn} />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {tab === 'investigation'
          ? <InvestigationConsole conn={conn} />
          : <CaseAnalysis conn={conn} />
        }
      </div>

      <footer style={{
        borderTop: `1px solid ${C.border}`,
        padding: '0.55rem 1.5rem',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: '0.6rem', color: C.dim, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          CaseMind Sentinel v0.4 · Build 3
        </span>
        {versionData && (
          <span style={{ fontSize: '0.6rem', color: C.dim, fontFamily: 'monospace' }}>
            backend {versionData.version}
          </span>
        )}
      </footer>
    </div>
  )
}
