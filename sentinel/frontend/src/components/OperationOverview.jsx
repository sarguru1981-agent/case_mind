import { C } from '../tokens'

const CASE_COLORS = [C.cyan, C.blue, C.green, C.orange]

function fileToId(filename) {
  return filename.replace('.txt', '').split('-').slice(0, 2).join('-')
}

function caseShortName(filename) {
  const parts = filename.replace('.txt', '').split('-')
  if (parts.length >= 3) return parts.slice(2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  return filename
}

const STATUS_META = {
  COMPLETE:         { color: C.green,  label: 'ARCHIVE INVESTIGATION\nCOMPLETE' },
  ARCHIVE_BOUNDARY: { color: C.orange, label: 'ARCHIVE BOUNDARY' },
  SEARCHING:        { color: C.yellow, label: 'SEARCHING' },
  PLANNING:         { color: C.blue,   label: 'PLANNING' },
}

export default function OperationOverview({ result, conn }) {
  const statusMeta = result ? (STATUS_META[result.status] || { color: C.muted, label: result.status }) : null
  const files = result?.archive_sources || []

  const hitsByFile = {}
  for (const hit of result?.evidence_hits || []) {
    hitsByFile[hit.source_file] = (hitsByFile[hit.source_file] || 0) + 1
  }
  const maxHits = Math.max(...Object.values(hitsByFile), 1)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>

      {/* Operation card */}
      <div style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderTop: `2px solid ${C.cyan}`,
        borderRadius: 6,
        padding: '0.75rem 0.85rem',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: `radial-gradient(ellipse at 50% 0%, ${C.cyanBg} 0%, transparent 70%)`,
          pointerEvents: 'none',
        }} />
        <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.18em', color: C.cyan + '99', marginBottom: '0.3rem' }}>
          Active Operation
        </div>
        <div style={{ fontSize: '0.9rem', fontWeight: 800, color: C.white, letterSpacing: '0.04em', marginBottom: '0.15rem' }}>
          OPERATION NIGHTFALL
        </div>
        <div style={{ fontSize: '0.7rem', color: C.muted }}>
          Multi-Case Robbery Investigation
        </div>
        <div style={{ marginTop: '0.6rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '0.58rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
            color: C.cyan, background: C.cyanBg, border: `1px solid ${C.cyanBrd}`,
            borderRadius: 3, padding: '0.12rem 0.5rem',
          }}>
            4 Case Files
          </span>
          <span style={{
            fontSize: '0.58rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
            color: C.muted, background: C.border + '40', border: `1px solid ${C.border}`,
            borderRadius: 3, padding: '0.12rem 0.5rem',
          }}>
            Serial Robbery
          </span>
        </div>
      </div>

      {/* Status */}
      {result && statusMeta && (
        <div style={{
          background: C.surface,
          border: `1px solid ${statusMeta.color + '50'}`,
          borderRadius: 6,
          padding: '0.65rem 0.85rem',
          display: 'flex', alignItems: 'center', gap: '0.75rem',
        }}>
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: statusMeta.color,
            boxShadow: `0 0 8px ${statusMeta.color}`,
            flexShrink: 0,
          }} />
          <div>
            {statusMeta.label.split('\n').map((line, i) => (
              <div key={i} style={{
                fontSize: i === 0 ? '0.6rem' : '0.72rem',
                fontWeight: i === 1 ? 800 : 500,
                textTransform: 'uppercase',
                letterSpacing: i === 0 ? '0.08em' : '0.06em',
                color: i === 0 ? statusMeta.color + 'aa' : statusMeta.color,
                lineHeight: 1.2,
              }}>
                {line}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mission objective */}
      {result && (
        <div style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 6,
          padding: '0.65rem 0.85rem',
        }}>
          <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.35rem' }}>
            Mission Objective
          </div>
          <p style={{ fontSize: '0.75rem', color: C.text, lineHeight: 1.55 }}>
            {result.objective}
          </p>
        </div>
      )}

      {/* Archive coverage */}
      {files.length > 0 && (
        <div style={{
          background: C.surface,
          border: `1px solid ${C.border}`,
          borderRadius: 6,
          overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.5rem 0.85rem',
            borderBottom: `1px solid ${C.border}`,
            fontSize: '0.52rem', textTransform: 'uppercase',
            letterSpacing: '0.14em', color: C.muted,
          }}>
            Archive Coverage — {files.length} case files
          </div>
          <div style={{ padding: '0.6rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
            {files.map((file, i) => {
              const caseId = fileToId(file)
              const name = caseShortName(file)
              const hits = hitsByFile[file] || 0
              const pct = maxHits > 0 ? (hits / maxHits) * 100 : 0
              const color = CASE_COLORS[i % CASE_COLORS.length]
              return (
                <div key={file}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.62rem', color, fontWeight: 700 }}>
                      {caseId}
                    </span>
                    <span style={{ fontSize: '0.62rem', color: C.dim }}>
                      {hits > 0 ? `${hits} hits` : 'searched'}
                    </span>
                  </div>
                  <div style={{ height: 3, background: C.border, borderRadius: 2, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: hits > 0 ? `${pct}%` : '100%',
                      background: hits > 0 ? color : C.dim,
                      borderRadius: 2,
                      opacity: hits > 0 ? 1 : 0.3,
                    }} />
                  </div>
                  <div style={{ fontSize: '0.6rem', color: C.dim, marginTop: '0.15rem' }}>{name}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Backend status */}
      <div style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: 6,
        padding: '0.5rem 0.85rem',
        display: 'flex', alignItems: 'center', gap: '0.5rem',
      }}>
        <div style={{
          width: 6, height: 6, borderRadius: '50%',
          background: conn === 'connected' ? C.green : conn === 'checking' ? C.yellow : C.red,
          flexShrink: 0,
        }} />
        <span style={{ fontSize: '0.65rem', color: C.muted }}>
          {conn === 'connected' ? 'Backend connected' : conn === 'checking' ? 'Connecting…' : 'Backend offline'}
        </span>
      </div>
    </div>
  )
}
