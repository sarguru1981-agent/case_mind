import { useState } from 'react'
import { C } from '../tokens'

const EVENT_META = {
  PLAN_CREATED:             { color: C.cyan,   icon: '◆', label: 'Plan' },
  SEARCH_STARTED:           { color: C.yellow, icon: '⊕', label: 'Search' },
  EVIDENCE_FOUND:           { color: C.green,  icon: '●', label: 'Evidence' },
  LEAD_DISCOVERED:          { color: C.orange, icon: '◈', label: 'Lead' },
  SEARCH_UPDATED:           { color: C.blue,   icon: '→', label: 'Decision' },
  ARCHIVE_BOUNDARY_REACHED: { color: C.red,    icon: '⊘', label: 'Boundary' },
  INVESTIGATION_COMPLETE:   { color: C.green,  icon: '✓', label: 'Complete' },
}

export default function InvestigationTimeline({ timeline }) {
  const [expanded, setExpanded] = useState(new Set(['LEAD_DISCOVERED', 'ARCHIVE_BOUNDARY_REACHED', 'INVESTIGATION_COMPLETE']))
  const [showAll, setShowAll] = useState(false)

  if (!timeline || timeline.length === 0) return null

  const toggleType = (type) => {
    setExpanded(prev => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
    }}>
      <div style={{
        padding: '0.55rem 0.85rem',
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.muted }}>
          Investigation Timeline
        </span>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: C.dim }}>
            {timeline.length} events
          </span>
          <button
            onClick={() => setShowAll(v => !v)}
            style={{
              background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 3,
              color: C.dim, cursor: 'pointer', fontSize: '0.5rem',
              padding: '0.1rem 0.4rem', textTransform: 'uppercase', letterSpacing: '0.08em',
            }}
          >
            {showAll ? '▲ compact' : '▼ expand'}
          </button>
        </div>
      </div>

      <div style={{ overflowY: 'auto', maxHeight: showAll ? 520 : 220 }}>
        {timeline.map((evt, i) => {
          const meta = EVENT_META[evt.type] || { color: C.muted, icon: '·', label: evt.type }
          const isLast = i === timeline.length - 1
          const showSummary = expanded.has(evt.type)

          return (
            <div
              key={i}
              onClick={() => toggleType(evt.type)}
              style={{
                padding: '0.45rem 0.85rem',
                borderBottom: isLast ? 'none' : `1px solid ${C.border}`,
                display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
                cursor: 'pointer',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = C.glass}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                <span style={{ color: meta.color, fontSize: '0.75rem', lineHeight: 1, width: 14, textAlign: 'center' }}>
                  {meta.icon}
                </span>
                {!isLast && (
                  <div style={{ width: 1, flex: 1, background: C.border, marginTop: '0.3rem', minHeight: 6 }} />
                )}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '0.6rem', fontWeight: 700, color: meta.color,
                    textTransform: 'uppercase', letterSpacing: '0.08em',
                  }}>
                    {meta.label}
                  </span>
                  {evt.hop != null && (
                    <span style={{ fontFamily: 'monospace', fontSize: '0.58rem', color: C.dim }}>
                      hop {evt.hop}
                    </span>
                  )}
                </div>

                {evt.query && evt.type === 'SEARCH_STARTED' && (
                  <div style={{
                    fontFamily: 'monospace', fontSize: '0.65rem', color: C.cyan + 'cc',
                    marginTop: '0.15rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  }}>
                    "{evt.query}"
                  </div>
                )}

                {showSummary && evt.summary && (
                  <p style={{ fontSize: '0.72rem', color: C.muted, lineHeight: 1.5, marginTop: '0.15rem' }}>
                    {evt.summary}
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
