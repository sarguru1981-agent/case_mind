import { C } from '../tokens'

const CASE_COLORS = [C.cyan, C.blue, C.green, C.orange]

function fileToId(filename) {
  return filename.replace('.txt', '').split('-').slice(0, 2).join('-')
}

function caseShortName(filename) {
  const parts = filename.replace('.txt', '').split('-')
  if (parts.length >= 3) {
    return parts.slice(2).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }
  return filename
}

function DonutChart({ segments }) {
  const total = segments.reduce((s, d) => s + d.count, 0)
  if (total === 0) return null
  const cx = 52, cy = 52, R = 40, IR = 26
  let angle = -Math.PI / 2

  const arcs = segments.map(seg => {
    if (seg.count === 0) return null
    const sweep = (seg.count / total) * 2 * Math.PI
    const x1 = cx + R * Math.cos(angle)
    const y1 = cy + R * Math.sin(angle)
    const x2 = cx + R * Math.cos(angle + sweep)
    const y2 = cy + R * Math.sin(angle + sweep)
    const xi1 = cx + IR * Math.cos(angle + sweep)
    const yi1 = cy + IR * Math.sin(angle + sweep)
    const xi2 = cx + IR * Math.cos(angle)
    const yi2 = cy + IR * Math.sin(angle)
    const large = sweep > Math.PI ? 1 : 0
    const d = `M${x1},${y1} A${R},${R} 0 ${large},1 ${x2},${y2} L${xi1},${yi1} A${IR},${IR} 0 ${large},0 ${xi2},${yi2} Z`
    angle += sweep
    return { d, color: seg.color }
  })

  return (
    <svg width={104} height={104} viewBox="0 0 104 104" style={{ flexShrink: 0 }}>
      {arcs.map((arc, i) => arc && (
        <path key={i} d={arc.d} fill={arc.color} opacity={0.85} />
      ))}
      <circle cx={cx} cy={cy} r={IR - 2} fill={C.surface} />
      <text x={cx} y={cy - 4} textAnchor="middle" dominantBaseline="middle"
            fontSize="14" fontWeight="800" fill={C.text} fontFamily="monospace">
        {total}
      </text>
      <text x={cx} y={cy + 10} textAnchor="middle"
            fontSize="7" fill={C.muted} fontFamily="sans-serif">
        HITS
      </text>
    </svg>
  )
}

export default function EvidenceOverview({ result }) {
  if (!result) return null

  const byFile = {}
  for (const hit of result.evidence_hits || []) {
    byFile[hit.source_file] = (byFile[hit.source_file] || 0) + 1
  }

  const files = Object.keys(byFile).sort()
  const max = Math.max(...Object.values(byFile), 1)

  const segments = files.map((f, i) => ({
    label: fileToId(f),
    name: caseShortName(f),
    count: byFile[f],
    color: CASE_COLORS[i % CASE_COLORS.length],
  }))

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
        fontSize: '0.55rem', textTransform: 'uppercase',
        letterSpacing: '0.15em', color: C.muted,
      }}>
        Archive Evidence Distribution
      </div>

      <div style={{ padding: '0.75rem 0.85rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <DonutChart segments={segments} />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {segments.map(seg => (
            <div key={seg.label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{
                  fontFamily: 'monospace', fontSize: '0.65rem',
                  color: seg.color, fontWeight: 700,
                }}>{seg.label}</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: C.muted }}>
                  {seg.count} hit{seg.count !== 1 ? 's' : ''}
                </span>
              </div>
              <div style={{
                height: 4, background: C.border, borderRadius: 2, overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%', width: `${(seg.count / max) * 100}%`,
                  background: seg.color, borderRadius: 2,
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
