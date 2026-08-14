import { C } from '../tokens'

const EXTERNAL_SYSTEMS = [
  { id: 'vehicle',   label: 'Vehicle Records',       icon: '▷', desc: 'DVLA / ANPR database' },
  { id: 'access',    label: 'Access Logs',            icon: '◇', desc: 'Northstar facility access' },
  { id: 'anpr',      label: 'ANPR Surveillance',      icon: '◉', desc: 'Camera network footage' },
  { id: 'financial', label: 'Financial Intelligence', icon: '◈', desc: 'Transaction trail analysis' },
]

export default function ArchiveBoundary({ signals, stoppingReason }) {
  const hasBoundary = signals && signals.length > 0
  if (!hasBoundary) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {/* Boundary header */}
      <div style={{
        background: C.redBg,
        border: `1px solid ${C.redBrd}`,
        borderLeft: `3px solid ${C.red}`,
        borderRadius: 6,
        padding: '0.65rem 0.85rem',
        display: 'flex', alignItems: 'center', gap: '0.65rem',
      }}>
        <span style={{ fontSize: '1.1rem', color: C.red, flexShrink: 0 }}>⊘</span>
        <div>
          <div style={{
            fontSize: '0.6rem', fontWeight: 800, textTransform: 'uppercase',
            letterSpacing: '0.12em', color: C.red,
          }}>
            Archive Boundary Reached
          </div>
          {stoppingReason && (
            <div style={{ fontSize: '0.68rem', color: C.muted, marginTop: '0.1rem' }}>
              {stoppingReason}
            </div>
          )}
        </div>
      </div>

      {/* External requirements list */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
        <div style={{
          padding: '0.5rem 0.85rem', borderBottom: `1px solid ${C.border}`,
          fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
        }}>
          Requires External Investigation
        </div>
        <div style={{ padding: '0.55rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {signals.map((s, i) => (
            <div key={i} style={{
              display: 'flex', gap: '0.5rem', alignItems: 'flex-start',
              padding: '0.35rem 0.55rem',
              background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4,
            }}>
              <span style={{ color: C.red, fontSize: '0.65rem', flexShrink: 0, marginTop: '0.1rem' }}>⊡</span>
              <span style={{ fontSize: '0.72rem', color: C.muted, lineHeight: 1.5 }}>{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* External system cards — all UNAVAILABLE */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
        <div style={{
          padding: '0.5rem 0.85rem', borderBottom: `1px solid ${C.border}`,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
            External Systems
          </span>
          <span style={{
            fontSize: '0.5rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
            color: C.orange, background: C.orangeBg, border: `1px solid ${C.orangeBrd}`,
            borderRadius: 3, padding: '0.08rem 0.4rem',
          }}>
            Coming in AI Agent Stage
          </span>
        </div>
        <div style={{
          padding: '0.55rem 0.85rem',
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.45rem',
        }}>
          {EXTERNAL_SYSTEMS.map(sys => (
            <div key={sys.id} style={{
              background: C.bg, border: `1px solid ${C.border}`, borderRadius: 5,
              padding: '0.5rem 0.65rem', display: 'flex', flexDirection: 'column', gap: '0.2rem',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: C.dim }}>{sys.icon}</span>
                <span style={{
                  fontSize: '0.46rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
                  color: C.dim, background: C.border, borderRadius: 2, padding: '0.05rem 0.35rem',
                }}>
                  UNAVAILABLE
                </span>
              </div>
              <div style={{ fontSize: '0.63rem', fontWeight: 700, color: C.muted, fontFamily: 'monospace' }}>
                {sys.label}
              </div>
              <div style={{ fontSize: '0.57rem', color: C.dim, lineHeight: 1.4 }}>{sys.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
