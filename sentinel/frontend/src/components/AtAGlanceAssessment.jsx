import { useState } from 'react'
import { C } from '../tokens'

export default function AtAGlanceAssessment({ result }) {
  const [showFull, setShowFull] = useState(false)
  if (!result) return null

  const incidents     = result.archive_sources?.length ?? 0
  const crossCaseLeads = (result.leads_discovered || []).filter(l => l.cases_found_in.length >= 2).length
  const externalReq   = result.requires_external_investigation?.length > 0

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.greenBrd}`,
      borderLeft: `3px solid ${C.green}`,
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.5rem 0.85rem',
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
          <span style={{ fontSize: '0.65rem', color: C.green }}>✓</span>
          <span style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.muted }}>
            At-a-Glance Assessment
          </span>
        </div>
        <button
          onClick={() => setShowFull(f => !f)}
          style={{
            background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 3,
            color: C.dim, cursor: 'pointer', fontSize: '0.52rem', padding: '0.12rem 0.5rem',
            textTransform: 'uppercase', letterSpacing: '0.08em',
          }}
        >
          {showFull ? '▲ hide' : '▼ full assessment'}
        </button>
      </div>

      <div style={{ padding: '0.6rem 0.85rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.35rem',
          background: C.cyanBg, border: `1px solid ${C.cyanBrd}`,
          borderRadius: 4, padding: '0.25rem 0.65rem',
        }}>
          <span style={{ fontFamily: 'monospace', fontSize: '0.9rem', fontWeight: 800, color: C.cyan }}>{incidents}</span>
          <span style={{ fontSize: '0.6rem', color: C.muted }}>incidents</span>
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.35rem',
          background: C.orangeBg, border: `1px solid ${C.orangeBrd}`,
          borderRadius: 4, padding: '0.25rem 0.65rem',
        }}>
          <span style={{ fontFamily: 'monospace', fontSize: '0.9rem', fontWeight: 800, color: C.orange }}>{crossCaseLeads}</span>
          <span style={{ fontSize: '0.6rem', color: C.muted }}>cross-case leads</span>
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.35rem',
          background: externalReq ? C.redBg : C.greenBg,
          border: `1px solid ${externalReq ? C.redBrd : C.greenBrd}`,
          borderRadius: 4, padding: '0.25rem 0.65rem',
        }}>
          <span style={{ fontSize: '0.62rem', fontWeight: 700, color: externalReq ? C.red : C.green }}>
            {externalReq ? '⊘ External required' : '✓ Archive resolved'}
          </span>
        </div>
      </div>

      {showFull && result.archive_level_conclusion && (
        <div style={{ padding: '0.65rem 0.85rem', borderTop: `1px solid ${C.border}`, background: C.bg }}>
          <p style={{ fontSize: '0.78rem', color: C.text, lineHeight: 1.65 }}>
            {result.archive_level_conclusion}
          </p>
        </div>
      )}
    </div>
  )
}
