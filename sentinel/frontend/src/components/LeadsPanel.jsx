import { useState } from 'react'
import { C } from '../tokens'

const LEAD_CATEGORY = {
  northstar_facilities:   { icon: '◉', type: 'Organization',      color: C.orange },
  daniel_mercer:          { icon: '◎', type: 'Person of Interest', color: C.yellow },
  credential_nf3847:      { icon: '◇', type: 'Credential Lead',    color: C.red    },
  dark_blue_transit:      { icon: '▷', type: 'Vehicle Lead',       color: C.blue   },
  alarm_maintenance_mode: { icon: '⬡', type: 'Tactic',            color: C.orange },
  sentryguard_pattern:    { icon: '◈', type: 'System',            color: C.cyan   },
}

function fmtLabel(s) {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function CaseChip({ caseId }) {
  const color = caseId.includes('001') || caseId.includes('003') ? C.cyan : C.blue
  return (
    <span style={{
      fontFamily: 'monospace', fontSize: '0.58rem', color,
      background: color + '18', border: `1px solid ${color + '35'}`,
      borderRadius: 3, padding: '0.1rem 0.45rem',
    }}>
      {caseId}
    </span>
  )
}

export default function LeadsPanel({ leads, selectedLeadId, onLeadSelect }) {
  const [expanded, setExpanded] = useState(null)

  if (!leads || leads.length === 0) return null

  const handleClick = (label) => {
    setExpanded(expanded === label ? null : label)
    if (onLeadSelect) onLeadSelect(selectedLeadId === label ? null : label)
  }

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 6,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.55rem 0.85rem',
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.muted }}>
          Discovered Leads
        </span>
        <span style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: C.orange }}>
          {leads.length} total
        </span>
      </div>

      <div>
        {leads.map((lead, i) => {
          const meta = LEAD_CATEGORY[lead.label] || { icon: '·', type: 'Lead', color: C.muted }
          const crossCase = lead.cases_found_in.length >= 2
          const isOpen = expanded === lead.label
          const isSel = selectedLeadId === lead.label
          const isLast = i === leads.length - 1

          return (
            <div
              key={lead.label}
              style={{
                borderBottom: isLast ? 'none' : `1px solid ${C.border}`,
                borderLeft: `3px solid ${isSel ? meta.color : meta.color + '60'}`,
                background: isSel ? meta.color + '08' : 'transparent',
                transition: 'all 0.15s',
              }}
            >
              <div
                onClick={() => handleClick(lead.label)}
                style={{
                  padding: '0.55rem 0.75rem',
                  cursor: 'pointer',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                  gap: '0.5rem',
                }}
                onMouseEnter={e => { if (!isSel) e.currentTarget.style.background = C.glass }}
                onMouseLeave={e => { if (!isSel) e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                    <span style={{ color: meta.color, fontSize: '0.85rem' }}>{meta.icon}</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: meta.color, letterSpacing: '-0.01em' }}>
                      {fmtLabel(lead.label)}
                    </span>
                    {crossCase && (
                      <span style={{
                        fontSize: '0.52rem', fontWeight: 700, textTransform: 'uppercase',
                        letterSpacing: '0.1em', color: C.orange,
                        background: C.orangeBg, border: `1px solid ${C.orangeBrd}`,
                        borderRadius: 3, padding: '0.08rem 0.4rem',
                      }}>
                        Cross-Case
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.6rem', color: C.dim, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {meta.type} · {lead.cases_found_in.length} case{lead.cases_found_in.length !== 1 ? 's' : ''}
                  </div>
                </div>
                <span style={{ fontSize: '0.6rem', color: isSel ? meta.color : C.dim, flexShrink: 0, marginTop: '0.1rem' }}>
                  {isOpen ? '▲' : '▼'}
                </span>
              </div>

              {isOpen && (
                <div style={{
                  padding: '0.5rem 0.75rem 0.65rem 1.1rem',
                  borderTop: `1px solid ${C.border}`,
                  background: C.bg,
                }}>
                  <p style={{ fontSize: '0.775rem', color: C.muted, lineHeight: 1.55, marginBottom: '0.5rem' }}>
                    {lead.context}
                  </p>
                  <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                    {lead.cases_found_in.map(c => <CaseChip key={c} caseId={c} />)}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
