import { useState } from 'react'
import { C } from '../tokens'

function shortQuery(q) {
  if (!q) return '…'
  const words = q.trim().split(/\s+/)
  return words.slice(0, 3).join(' ') + (words.length > 3 ? '…' : '')
}

export default function InvestigationPlan({ plan, timeline }) {
  const [activeHop, setActiveHop] = useState(null)

  const hops = (timeline || []).filter(e => e.type === 'SEARCH_STARTED')

  const steps = hops.length > 0
    ? hops.map(e => ({ hop: e.hop ?? 1, query: e.query || '', label: shortQuery(e.query) }))
    : (plan ? [{ hop: 1, query: plan.initial_query || '', label: shortQuery(plan.initial_query) }] : [])

  if (steps.length === 0) return null

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
          Investigation Plan
        </span>
        <span style={{
          fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.1em',
          color: C.green, background: C.greenBg, border: `1px solid ${C.greenBrd}`,
          borderRadius: 3, padding: '0.1rem 0.45rem',
        }}>
          {steps.length} hops executed
        </span>
      </div>

      <div style={{ padding: '0.75rem 0.85rem' }}>
        {/* Visual hop progression */}
        <div style={{ display: 'flex', alignItems: 'center', overflowX: 'auto', paddingBottom: '0.3rem' }}>
          {steps.map((step, i) => (
            <div key={step.hop} style={{ display: 'flex', alignItems: 'center' }}>
              <div
                onClick={() => setActiveHop(activeHop === step.hop ? null : step.hop)}
                style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', cursor: 'pointer', minWidth: 56 }}
              >
                <div style={{
                  width: activeHop === step.hop ? 28 : 22,
                  height: activeHop === step.hop ? 28 : 22,
                  borderRadius: '50%',
                  background: activeHop === step.hop ? C.cyan : C.cyanBg,
                  border: `2px solid ${C.cyan}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.65rem', fontWeight: 800,
                  color: activeHop === step.hop ? C.bg : C.cyan,
                  fontFamily: 'monospace',
                  transition: 'all 0.15s',
                  boxShadow: activeHop === step.hop ? `0 0 10px ${C.cyan}55` : 'none',
                  flexShrink: 0,
                }}>
                  {step.hop}
                </div>
                <div style={{
                  fontSize: '0.52rem', color: activeHop === step.hop ? C.cyan : C.dim,
                  marginTop: '0.25rem', textAlign: 'center', maxWidth: 54,
                  whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  fontFamily: 'monospace',
                  transition: 'color 0.15s',
                }}>
                  {step.label}
                </div>
              </div>
              {i < steps.length - 1 && (
                <div style={{
                  width: 20, height: 2,
                  background: `linear-gradient(90deg, ${C.cyan}80, ${C.cyan}40)`,
                  flexShrink: 0, marginBottom: 18,
                }} />
              )}
            </div>
          ))}

          {/* Archive boundary cap */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: 20, height: 2, background: C.dim + '50', flexShrink: 0, marginBottom: 18 }} />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 56 }}>
              <div style={{
                width: 22, height: 22, borderRadius: '50%',
                background: C.redBg, border: `2px solid ${C.red}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.72rem', color: C.red,
              }}>⊘</div>
              <div style={{ fontSize: '0.52rem', color: C.dim, marginTop: '0.25rem', textAlign: 'center', maxWidth: 54 }}>
                boundary
              </div>
            </div>
          </div>
        </div>

        {/* Active hop detail */}
        {activeHop !== null && (
          <div style={{
            marginTop: '0.6rem',
            padding: '0.45rem 0.65rem',
            background: C.cyanBg, border: `1px solid ${C.cyanBrd}`,
            borderRadius: 4,
          }}>
            <div style={{
              fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.1em',
              color: C.dim, marginBottom: '0.2rem',
            }}>
              Hop {activeHop} — search query
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: C.cyan }}>
              "{steps.find(s => s.hop === activeHop)?.query}"
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
