import { useState } from 'react'
import { C } from '../tokens'

const CASE_POS = {
  'robbery-001': { x: 110, y: 90,  label: 'Hawthorne\nJewellers',      short: 'ROB-001', color: C.cyan },
  'robbery-002': { x: 690, y: 90,  label: 'Millbrook\nGallery',        short: 'ROB-002', color: C.blue },
  'robbery-003': { x: 110, y: 350, label: 'Bellweather\nElectronics',  short: 'ROB-003', color: C.cyan },
  'robbery-004': { x: 690, y: 350, label: 'Kingsley\nWatches',         short: 'ROB-004', color: C.blue },
}

const LEAD_META = {
  northstar_facilities:   { label: 'Northstar Facilities', type: 'ORG',        color: C.orange },
  daniel_mercer:          { label: 'Daniel Mercer',        type: 'PERSON',     color: C.yellow },
  credential_nf3847:      { label: 'Credential NF-3847',   type: 'CREDENTIAL', color: C.red    },
  dark_blue_transit:      { label: 'Dark Blue Transit',    type: 'VEHICLE',    color: C.blue   },
  alarm_maintenance_mode: { label: 'Alarm Mode',           type: 'TACTIC',     color: C.orange },
  sentryguard_pattern:    { label: 'SentryGuard',          type: 'SYSTEM',     color: C.cyan   },
}

const TYPE_ABBR = {
  ORG: 'ORG', PERSON: 'PSN', CREDENTIAL: 'CRD',
  VEHICLE: 'VEH', TACTIC: 'TAC', SYSTEM: 'SYS',
}

function fileToId(filename) {
  return filename.replace('.txt', '').split('-').slice(0, 2).join('-')
}

function edgePath(from, to) {
  const mx = (from.x + to.x) / 2
  const my = (from.y + to.y) / 2
  const cx = 400, cy = 220
  const bx = mx + (cx - mx) * 0.18
  const by = my + (cy - my) * 0.18
  return `M${from.x},${from.y} Q${bx},${by} ${to.x},${to.y}`
}

function buildGraph(result) {
  if (!result) return { caseNodes: [], leadNodes: [], edges: [] }

  const CX = 400, CY = 220

  const caseNodes = (result.archive_sources || []).map(file => {
    const id = fileToId(file)
    const pos = CASE_POS[id]
    if (!pos) return null
    return { id, ...pos }
  }).filter(Boolean)

  const leads = result.leads_discovered || []
  const n = leads.length || 1
  const leadNodes = leads.map((lead, i) => {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
    const meta = LEAD_META[lead.label] || { label: lead.label, type: 'ENTITY', color: C.muted }
    return {
      id: lead.label,
      x: CX + 145 * Math.cos(angle),
      y: CY + 105 * Math.sin(angle),
      ...meta,
      lead,
    }
  })

  const edges = []
  for (const ln of leadNodes) {
    for (const caseId of (ln.lead.cases_found_in || [])) {
      const cn = caseNodes.find(c => c.id === caseId)
      if (cn) {
        edges.push({
          from: cn, to: ln,
          crossCase: ln.lead.cases_found_in.length >= 2,
        })
      }
    }
  }

  return { caseNodes, leadNodes, edges }
}

function PlaceholderGraph() {
  const cases = Object.entries(CASE_POS)
  const cx = 400, cy = 220
  return (
    <g>
      <circle cx={cx} cy={cy} r={38} fill={C.surface} stroke={C.border} strokeWidth={1} />
      <text x={cx} y={cy - 8} textAnchor="middle" fill={C.dim} fontSize="10" fontFamily="monospace">ARCHIVE</text>
      <text x={cx} y={cy + 8} textAnchor="middle" fill={C.dim} fontSize="10" fontFamily="monospace">PENDING</text>
      {cases.map(([id, pos]) => (
        <line key={id} x1={pos.x} y1={pos.y} x2={cx} y2={cy}
          stroke={C.dim} strokeWidth={1} strokeDasharray="4,4" opacity={0.4} />
      ))}
      {cases.map(([id, pos]) => (
        <g key={id}>
          <rect x={pos.x - 42} y={pos.y - 24} width={84} height={48} rx={4}
            fill={C.surface} stroke={C.border} strokeWidth={1} />
          <text x={pos.x} y={pos.y - 10} textAnchor="middle" fill={pos.color} fontSize="9"
            fontFamily="monospace" fontWeight="700">{pos.short}</text>
          {pos.label.split('\n').map((line, i) => (
            <text key={i} x={pos.x} y={pos.y + 5 + i * 12} textAnchor="middle"
              fill={C.muted} fontSize="8" fontFamily="sans-serif">{line}</text>
          ))}
        </g>
      ))}
    </g>
  )
}

export default function RelationshipGraph({ result, selectedNodeId, onNodeSelect }) {
  const [hovered, setHovered] = useState(null)
  const { caseNodes, leadNodes, edges } = buildGraph(result)
  const hasData = leadNodes.length > 0

  const activeId = selectedNodeId || hovered

  const connectedIds = new Set()
  if (activeId) {
    connectedIds.add(activeId)
    for (const e of edges) {
      if (e.from.id === activeId || e.to.id === activeId) {
        connectedIds.add(e.from.id)
        connectedIds.add(e.to.id)
      }
    }
  }

  const nodeOpacity = (id) => {
    if (!activeId) return 1
    return connectedIds.has(id) ? 1 : 0.15
  }

  const edgeOpacity = (e) => {
    if (!activeId) return e.crossCase ? 0.55 : 0.25
    return (e.from.id === activeId || e.to.id === activeId) ? 0.95 : 0.07
  }

  const handleNodeClick = (id) => {
    if (onNodeSelect) onNodeSelect(selectedNodeId === id ? null : id)
  }

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${selectedNodeId ? C.cyanBrd : C.border}`,
      borderRadius: 6,
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      <div style={{
        padding: '0.55rem 0.85rem',
        borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.muted }}>
          Evidence Relationship Network
        </span>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {selectedNodeId && (
            <span
              onClick={() => onNodeSelect && onNodeSelect(null)}
              style={{
                fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.1em',
                color: C.cyan, background: C.cyanBg, border: `1px solid ${C.cyanBrd}`,
                borderRadius: 3, padding: '0.1rem 0.45rem', cursor: 'pointer',
              }}
            >
              × clear
            </span>
          )}
          {hasData && (
            <span style={{
              fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.1em',
              color: C.green, background: C.greenBg, border: `1px solid ${C.greenBrd}`,
              borderRadius: 3, padding: '0.1rem 0.45rem',
            }}>
              {leadNodes.length} leads · {edges.length} connections
            </span>
          )}
        </div>
      </div>

      <svg
        viewBox="0 0 800 440"
        style={{ width: '100%', display: 'block', background: C.bg }}
        aria-label="Investigation relationship network"
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <filter id="glow-strong">
            <feGaussianBlur stdDeviation="6" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {[88, 176, 264, 352].map(y => (
          <line key={y} x1={0} y1={y} x2={800} y2={y} stroke={C.border} strokeWidth={0.5} opacity={0.4} />
        ))}
        {[160, 320, 480, 640].map(x => (
          <line key={x} x1={x} y1={0} x2={x} y2={440} stroke={C.border} strokeWidth={0.5} opacity={0.4} />
        ))}

        {!hasData && <PlaceholderGraph />}

        {hasData && (
          <>
            {edges.map((e, i) => {
              const isActive = e.from.id === activeId || e.to.id === activeId
              return (
                <path
                  key={i}
                  d={edgePath(e.from, e.to)}
                  stroke={e.crossCase ? C.cyan : C.borderHi}
                  strokeWidth={e.crossCase ? (isActive ? 2.5 : 1.5) : (isActive ? 2 : 1)}
                  fill="none"
                  opacity={edgeOpacity(e)}
                  strokeDasharray={e.crossCase ? '6,3' : undefined}
                  style={e.crossCase ? { animation: 'dash-flow 1.5s linear infinite' } : undefined}
                />
              )
            })}

            {leadNodes.map(ln => {
              const isHov = hovered === ln.id
              const isSel = selectedNodeId === ln.id
              const crossCase = (ln.lead.cases_found_in || []).length >= 2
              const r = isSel ? 27 : isHov ? 25 : 22
              return (
                <g
                  key={ln.id}
                  onMouseEnter={() => setHovered(ln.id)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => handleNodeClick(ln.id)}
                  style={{ cursor: 'pointer', opacity: nodeOpacity(ln.id), transition: 'opacity 0.2s' }}
                >
                  {crossCase && (
                    <circle cx={ln.x} cy={ln.y} r={r + 9}
                      fill="none" stroke={ln.color} strokeWidth={1}
                      opacity={isSel ? 0.55 : isHov ? 0.35 : 0.18}
                      style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}
                    />
                  )}
                  <circle
                    cx={ln.x} cy={ln.y} r={r}
                    fill={isSel ? ln.color + '38' : ln.color + '20'}
                    stroke={ln.color}
                    strokeWidth={isSel ? 2.5 : isHov ? 2 : 1.5}
                    filter={isSel ? 'url(#glow-strong)' : isHov ? 'url(#glow)' : undefined}
                  />
                  <text x={ln.x} y={ln.y - 5} textAnchor="middle"
                    fill={ln.color} fontSize="7.5" fontFamily="monospace"
                    fontWeight="700" dominantBaseline="middle">
                    {TYPE_ABBR[ln.type] || ln.type}
                  </text>
                  <text x={ln.x} y={ln.y + 8} textAnchor="middle"
                    fill={ln.color + 'cc'} fontSize="8" fontFamily="monospace"
                    dominantBaseline="middle">
                    {ln.lead.cases_found_in.length}×
                  </text>
                  <text x={ln.x} y={ln.y + 34} textAnchor="middle"
                    fill={isSel ? C.white : isHov ? C.text : C.muted} fontSize="8.5"
                    fontFamily="sans-serif" style={{ transition: 'fill 0.15s' }}>
                    {ln.label}
                  </text>
                </g>
              )
            })}

            {caseNodes.map(cn => {
              const isHov = hovered === cn.id
              const isSel = selectedNodeId === cn.id
              const lines = cn.label.split('\n')
              return (
                <g
                  key={cn.id}
                  onMouseEnter={() => setHovered(cn.id)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => handleNodeClick(cn.id)}
                  style={{ cursor: 'pointer', opacity: nodeOpacity(cn.id), transition: 'opacity 0.2s' }}
                >
                  <rect
                    x={cn.x - 44} y={cn.y - 29}
                    width={88} height={58}
                    rx={5}
                    fill={isSel ? cn.color + '28' : isHov ? cn.color + '18' : C.surface}
                    stroke={cn.color}
                    strokeWidth={isSel ? 2 : isHov ? 1.5 : 1}
                    filter={isSel ? 'url(#glow-strong)' : isHov ? 'url(#glow)' : undefined}
                    style={{ transition: 'all 0.15s' }}
                  />
                  <text x={cn.x} y={cn.y - 14} textAnchor="middle"
                    fill={cn.color} fontSize="9" fontFamily="monospace" fontWeight="700">
                    {cn.short}
                  </text>
                  {lines.map((line, i) => (
                    <text key={i} x={cn.x} y={cn.y + 4 + i * 12}
                      textAnchor="middle"
                      fill={isSel ? C.text : isHov ? C.text : C.muted} fontSize="8"
                      fontFamily="sans-serif">
                      {line}
                    </text>
                  ))}
                </g>
              )
            })}
          </>
        )}
      </svg>

      <div style={{
        padding: '0.45rem 0.85rem',
        borderTop: `1px solid ${C.border}`,
        display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center',
      }}>
        {selectedNodeId ? (
          <span style={{ fontSize: '0.58rem', color: C.cyan, fontFamily: 'monospace' }}>
            Click same node to deselect · Click another to switch
          </span>
        ) : (
          <>
            {[
              { color: C.cyan,   label: 'Cross-case link' },
              { color: C.orange, label: 'Org / Tactic' },
              { color: C.yellow, label: 'Person' },
              { color: C.red,    label: 'Credential' },
              { color: C.blue,   label: 'Vehicle / System' },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                <span style={{ fontSize: '0.58rem', color: C.muted }}>{label}</span>
              </div>
            ))}
            <span style={{ fontSize: '0.55rem', color: C.dim, marginLeft: 'auto' }}>Click node to investigate</span>
          </>
        )}
      </div>
    </div>
  )
}
