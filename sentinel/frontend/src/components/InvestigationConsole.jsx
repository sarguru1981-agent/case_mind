import { useState } from 'react'
import { C } from '../tokens'
import OperationOverview from './OperationOverview'
import MetricCard from './MetricCard'
import RelationshipGraph from './RelationshipGraph'
import InvestigationPlan from './InvestigationPlan'
import InvestigationTimeline from './InvestigationTimeline'
import LeadsPanel from './LeadsPanel'
import EvidenceOverview from './EvidenceOverview'
import ArchiveBoundary from './ArchiveBoundary'
import AtAGlanceAssessment from './AtAGlanceAssessment'
import IntelligenceDrawer from './IntelligenceDrawer'
import AgentInvestigationConsole from './AgentInvestigationConsole'

const BACKEND = 'http://localhost:8000'

const DEFAULT_OBJECTIVE =
  'Are the four Operation Nightfall robberies connected? ' +
  'Identify the strongest shared leads using only the police case archive.'

// ── Agentic RAG flow explanation bar ─────────────────────────────────────────

function FlowBadge({ label, active, complete }) {
  const color = complete ? C.green : active ? C.cyan : C.dim
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
      <div style={{
        width: 7, height: 7, borderRadius: '50%',
        background: color,
        boxShadow: active ? `0 0 6px ${color}` : 'none',
      }} />
      <span style={{
        fontSize: '0.58rem', fontWeight: active || complete ? 700 : 400,
        textTransform: 'uppercase', letterSpacing: '0.1em', color,
      }}>
        {label}
      </span>
    </div>
  )
}

function FlowArrow() {
  return <span style={{ color: C.dim, fontSize: '0.7rem' }}>→</span>
}

function AgenticRagFlow({ running, result }) {
  const done = !!result
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', padding: '0.4rem 0' }}>
      <FlowBadge label="Plan"             complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="Search"           complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="Evidence"         complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="New Lead"         complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="Search Updated"   complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="Search Again"     complete={done} active={running} />
      <FlowArrow />
      <FlowBadge label="Archive Boundary" complete={done} active={false} />
    </div>
  )
}

// ── Loading state ─────────────────────────────────────────────────────────────

function LoadingState({ objective }) {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '3rem 2rem', gap: '1.5rem',
    }}>
      <svg width={180} height={180} viewBox="0 0 180 180">
        {[60, 45, 30].map((r, i) => (
          <circle key={r} cx={90} cy={90} r={r}
            fill="none"
            stroke={i === 0 ? C.cyan : i === 1 ? C.blue : C.cyan}
            strokeWidth={i === 1 ? 1.5 : 1}
            opacity={i === 1 ? 0.6 : 0.3}
            strokeDasharray={i === 0 ? '6,4' : i === 2 ? '2,3' : undefined}
            style={{ animation: `pulse-glow ${1.5 + i * 0.4}s ease-in-out infinite` }}
          />
        ))}
        <text x={90} y={85} textAnchor="middle" fill={C.cyan} fontSize="11" fontFamily="monospace" fontWeight="700">
          ARCHIVE
        </text>
        <text x={90} y={100} textAnchor="middle" fill={C.cyan} fontSize="11" fontFamily="monospace" fontWeight="700">
          SEARCH
        </text>
        {[
          { cx: 28, cy: 28,  label: 'ROB-001' },
          { cx: 152, cy: 28,  label: 'ROB-002' },
          { cx: 28, cy: 152, label: 'ROB-003' },
          { cx: 152, cy: 152, label: 'ROB-004' },
        ].map(({ cx, cy, label }) => (
          <g key={label}>
            <line x1={cx} y1={cy} x2={90} y2={90}
              stroke={C.cyanBrd} strokeWidth={1} strokeDasharray="3,3"
              style={{ animation: 'dash-flow 1.5s linear infinite' }}
            />
            <circle cx={cx} cy={cy} r={14} fill={C.surface} stroke={C.cyan} strokeWidth={1}
              style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}
            />
            <text x={cx} y={cy + 4} textAnchor="middle" fill={C.cyan} fontSize="6" fontFamily="monospace">
              {label}
            </text>
          </g>
        ))}
      </svg>

      <div style={{ textAlign: 'center', maxWidth: 480 }}>
        <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.cyan, marginBottom: '0.5rem' }}>
          Archive Search In Progress
        </div>
        <p style={{ fontSize: '0.875rem', color: C.muted, lineHeight: 1.6, marginBottom: '1rem' }}>
          Running Search → Reason → Search loop across four Operation Nightfall case files…
        </p>
        <AgenticRagFlow running={true} result={null} />
      </div>
    </div>
  )
}

// ── Pre-run / mission briefing state ─────────────────────────────────────────

function PreRunState({ objective, setObjective, maxHops, setMaxHops, onRun, loading, conn }) {
  const canRun = objective.trim().length >= 10 && !loading && conn !== 'disconnected'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2.5rem 1.5rem' }}>
      <div style={{ width: '100%', maxWidth: 700 }}>

        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderTop: `2px solid ${C.cyan}`,
          borderRadius: 6, padding: '1.25rem 1.5rem', marginBottom: '1.25rem',
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '50%',
            background: `radial-gradient(ellipse at 30% 0%, ${C.cyanBg} 0%, transparent 70%)`,
            pointerEvents: 'none',
          }} />
          <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.18em', color: C.cyan, marginBottom: '0.75rem' }}>
            Agentic RAG · Operation Nightfall
          </div>
          <h1 style={{
            fontSize: '1.9rem', fontWeight: 800, color: C.white,
            lineHeight: 1.15, letterSpacing: '-0.025em', marginBottom: '0.65rem',
          }}>
            The archive<br />
            investigates<br />
            <span style={{ color: C.cyan }}>itself.</span>
          </h1>
          <p style={{ fontSize: '0.84rem', color: C.muted, lineHeight: 1.65, marginBottom: '1rem' }}>
            Build 3 — Search → Reason → Search. The investigation loop queries
            the four Operation Nightfall case files, following the strongest
            cross-case lead at each hop until it reaches the archive boundary.
          </p>
          <div style={{ padding: '0.7rem 0.85rem', background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4 }}>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.45rem' }}>
              Agentic RAG Cycle
            </div>
            <AgenticRagFlow running={false} result={null} />
          </div>
        </div>

        {/* Case files briefing — correct venue names */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '0.85rem 1.25rem', marginBottom: '1.25rem',
          display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap',
        }}>
          <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.12em', color: C.muted, flexShrink: 0 }}>
            Archive — 4 case files indexed
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {[
              ['robbery-001', 'Hawthorne Jewellers',    C.cyan],
              ['robbery-002', 'Millbrook Gallery',      C.blue],
              ['robbery-003', 'Bellweather Electronics', C.cyan],
              ['robbery-004', 'Kingsley Watches',       C.blue],
            ].map(([id, name, color]) => (
              <div key={id} style={{
                display: 'flex', alignItems: 'center', gap: '0.35rem',
                padding: '0.2rem 0.6rem',
                background: color + '12', border: `1px solid ${color + '30'}`,
                borderRadius: 4,
              }}>
                <div style={{ width: 5, height: 5, borderRadius: '50%', background: color }} />
                <span style={{ fontFamily: 'monospace', fontSize: '0.6rem', color, fontWeight: 700 }}>{id}</span>
                <span style={{ fontSize: '0.6rem', color: C.muted }}>{name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Investigation form */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
        }}>
          <div>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.4rem' }}>
              Investigation Objective
            </div>
            <textarea
              value={objective}
              onChange={e => setObjective(e.target.value)}
              style={{
                width: '100%', background: C.bg, border: `1px solid ${C.borderHi}`,
                borderRadius: 5, padding: '0.7rem 1rem', color: C.text,
                fontSize: '0.875rem', outline: 'none', resize: 'vertical',
                minHeight: 84, fontFamily: 'inherit', lineHeight: 1.55,
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <label style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
                Max Hops
              </label>
              <input
                type="number" min={1} max={10} value={maxHops}
                onChange={e => setMaxHops(Math.max(1, Math.min(10, parseInt(e.target.value, 10) || 5)))}
                style={{
                  width: 64, background: C.bg, border: `1px solid ${C.borderHi}`,
                  borderRadius: 5, padding: '0.4rem 0.75rem', color: C.text,
                  fontSize: '0.9rem', outline: 'none', textAlign: 'center', fontFamily: 'monospace',
                }}
              />
            </div>
            <button
              onClick={onRun}
              disabled={!canRun}
              style={{
                background: canRun ? C.btn : C.border,
                color: canRun ? C.white : C.dim,
                border: `1px solid ${canRun ? C.btn + 'aa' : C.border}`,
                borderRadius: 5, padding: '0.6rem 1.5rem',
                fontSize: '0.875rem', fontWeight: 700,
                cursor: canRun ? 'pointer' : 'not-allowed',
                letterSpacing: '0.02em', transition: 'all 0.15s',
                boxShadow: canRun ? `0 0 12px ${C.btn}40` : 'none',
              }}
            >
              Run Investigation
            </button>
          </div>

          {conn === 'disconnected' && (
            <div style={{
              padding: '0.5rem 0.75rem',
              background: C.redBg, border: `1px solid ${C.redBrd}`,
              borderRadius: 4, fontSize: '0.72rem', color: C.red, fontFamily: 'monospace',
            }}>
              Backend offline — cd sentinel/backend &amp;&amp; python3 -m uvicorn main:app --port 8000
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Post-run workstation layout ───────────────────────────────────────────────

function BoundaryStatusBadge({ result }) {
  const hasBoundary = result.requires_external_investigation?.length > 0
  return (
    <div style={{
      background: hasBoundary ? C.orangeBg : C.greenBg,
      border: `1px solid ${hasBoundary ? C.orangeBrd : C.greenBrd}`,
      borderRadius: 4, padding: '0.15rem 0.55rem',
      fontSize: '0.55rem', fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '0.1em', color: hasBoundary ? C.orange : C.green,
    }}>
      {hasBoundary ? '⊘ Boundary' : '✓ Resolved'}
    </div>
  )
}

function WorkstationHeader({ result, onReset }) {
  return (
    <div style={{
      padding: '0.55rem 1rem',
      borderBottom: `1px solid ${C.border}`,
      background: C.panel,
      display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: C.green, boxShadow: `0 0 6px ${C.green}` }} />
        <span style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: C.green }}>
          Archive Investigation Complete
        </span>
        <BoundaryStatusBadge result={result} />
      </div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
        {['Plan', '→', 'Search', '→', 'Evidence', '→', 'Lead', '→', 'Search', '→', 'Boundary'].map((item, i) => (
          item === '→'
            ? <span key={i} style={{ color: C.dim, fontSize: '0.6rem' }}>→</span>
            : <span key={i} style={{ fontSize: '0.55rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: C.green }}>{item}</span>
        ))}
      </div>

      <button
        onClick={onReset}
        style={{
          background: 'transparent', border: `1px solid ${C.border}`,
          borderRadius: 4, padding: '0.25rem 0.75rem',
          fontSize: '0.62rem', color: C.muted, cursor: 'pointer',
          letterSpacing: '0.06em', textTransform: 'uppercase',
        }}
      >
        New Investigation
      </button>
    </div>
  )
}

function IntelligenceCenter({ result, selectedNodeId, onNodeSelect }) {
  const searches = result.searches_performed
  const evidence = result.evidence_hits?.length ?? 0
  const leads    = result.leads_discovered?.length ?? 0
  const timeline = result.timeline?.length ?? 0
  const hasBoundary = result.requires_external_investigation?.length > 0

  return (
    <div className="ws-col">
      <div className="metrics-row">
        <MetricCard label="Search Hops"   value={searches} color={C.cyan}   icon="⊕" sub={`of ${result.plan?.max_hops} max`} />
        <MetricCard label="Evidence Hits" value={evidence} color={C.green}  icon="●" sub="retrieved chunks" />
        <MetricCard label="Leads Found"   value={leads}    color={C.orange} icon="◈" sub="cross-case entities" />
        <MetricCard label="Timeline"      value={timeline} color={C.blue}   icon="◆" sub="events logged" />
        <MetricCard
          label="Boundary"
          value={hasBoundary ? '⊘' : '✓'}
          color={hasBoundary ? C.orange : C.green}
          icon={hasBoundary ? '⊘' : '✓'}
          sub={hasBoundary ? 'reached' : 'resolved'}
        />
      </div>

      {/* Graph dominates — primary visual */}
      <RelationshipGraph
        result={result}
        selectedNodeId={selectedNodeId}
        onNodeSelect={onNodeSelect}
      />

      {/* Visual hop plan */}
      <InvestigationPlan plan={result.plan} timeline={result.timeline} />

      {/* Evidence distribution */}
      <EvidenceOverview result={result} />

      {/* Compact at-a-glance instead of full paragraph */}
      <AtAGlanceAssessment result={result} />
    </div>
  )
}

function SidePanel({ result, selectedNodeId, onNodeSelect }) {
  return (
    <div className="ws-col">
      {selectedNodeId
        ? (
          <IntelligenceDrawer
            selectedNodeId={selectedNodeId}
            result={result}
            onClose={() => onNodeSelect(null)}
          />
        )
        : (
          <>
            <LeadsPanel
              leads={result.leads_discovered}
              selectedLeadId={selectedNodeId}
              onLeadSelect={onNodeSelect}
            />
            <InvestigationTimeline timeline={result.timeline} />
            <ArchiveBoundary
              signals={result.requires_external_investigation}
              stoppingReason={result.stopping_reason}
            />
          </>
        )
      }
    </div>
  )
}

// ── Mode Selector ─────────────────────────────────────────────────────────────

function ModeSelector({ mode, setMode }) {
  const modes = [
    {
      id: 'rag', label: 'Agentic RAG', sublabel: 'Archive search loop',
      color: C.cyan, disabled: false,
    },
    {
      id: 'agent', label: 'AI Agent', sublabel: 'External tool investigation',
      color: C.blue, disabled: false,
    },
    {
      id: 'agentic-ai', label: 'Agentic AI', sublabel: 'Coming Later',
      color: C.dim, disabled: true,
    },
  ]

  return (
    <div style={{
      display: 'flex', borderBottom: `1px solid ${C.border}`,
      background: C.panel, flexShrink: 0,
    }}>
      {modes.map(m => {
        const active = mode === m.id
        return (
          <button
            key={m.id}
            disabled={m.disabled}
            onClick={() => !m.disabled && setMode(m.id)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
              padding: '0.5rem 1.25rem',
              background: active ? C.surface : 'transparent',
              border: 'none',
              borderRight: `1px solid ${C.border}`,
              borderBottom: `2px solid ${active ? m.color : 'transparent'}`,
              cursor: m.disabled ? 'not-allowed' : 'pointer',
              opacity: m.disabled ? 0.45 : 1,
              transition: 'all 0.15s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: active ? m.color : C.dim,
                boxShadow: active ? `0 0 5px ${m.color}` : 'none',
                transition: 'all 0.15s',
              }} />
              <span style={{
                fontSize: '0.65rem', fontWeight: active ? 800 : 500,
                textTransform: 'uppercase', letterSpacing: '0.1em',
                color: active ? m.color : C.muted,
              }}>
                {m.label}
              </span>
              {m.disabled && (
                <span style={{
                  fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.1em',
                  color: C.dim, background: C.bg, border: `1px solid ${C.border}`,
                  borderRadius: 2, padding: '0.06rem 0.3rem',
                }}>
                  Coming Later
                </span>
              )}
            </div>
            <span style={{
              fontSize: '0.52rem', letterSpacing: '0.06em', marginTop: '0.1rem',
              color: active ? m.color + 'aa' : C.dim,
            }}>
              {m.sublabel}
            </span>
          </button>
        )
      })}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function InvestigationConsole({ conn }) {
  const [mode, setMode] = useState('rag')

  // Agentic RAG state
  const [objective, setObjective]       = useState(DEFAULT_OBJECTIVE)
  const [maxHops, setMaxHops]           = useState(5)
  const [loading, setLoading]           = useState(false)
  const [result, setResult]             = useState(null)
  const [error, setError]               = useState(null)
  const [selectedNodeId, setSelectedNodeId] = useState(null)

  const run = async () => {
    if (!objective.trim() || loading) return
    setLoading(true); setResult(null); setError(null); setSelectedNodeId(null)
    try {
      const res = await fetch(`${BACKEND}/api/agentic-rag/investigate`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ objective: objective.trim(), max_hops: maxHops }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        setError(`HTTP ${res.status}: ${err.detail || res.statusText}`)
      } else {
        setResult(await res.json())
      }
    } catch (err) {
      setError(`Network error: ${String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const renderRagContent = () => {
    if (loading) return <LoadingState objective={objective} />

    if (!result) {
      return (
        <>
          {error && (
            <div style={{
              margin: '0.75rem 1.5rem', padding: '0.7rem 1rem',
              background: C.redBg, border: `1px solid ${C.redBrd}`,
              borderRadius: 6, fontFamily: 'monospace', fontSize: '0.78rem', color: C.red,
            }}>
              {error}
            </div>
          )}
          <PreRunState
            objective={objective} setObjective={setObjective}
            maxHops={maxHops}     setMaxHops={setMaxHops}
            onRun={run} loading={loading} conn={conn}
          />
        </>
      )
    }

    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <WorkstationHeader
          result={result}
          onReset={() => { setResult(null); setError(null); setSelectedNodeId(null) }}
        />
        <div className="investigation-workspace anim-slide-in">
          <OperationOverview result={result} conn={conn} />
          <IntelligenceCenter
            result={result}
            selectedNodeId={selectedNodeId}
            onNodeSelect={setSelectedNodeId}
          />
          <SidePanel
            result={result}
            selectedNodeId={selectedNodeId}
            onNodeSelect={setSelectedNodeId}
          />
        </div>
      </div>
    )
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <ModeSelector mode={mode} setMode={setMode} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
        {mode === 'rag' && renderRagContent()}
        {mode === 'agent' && <AgentInvestigationConsole conn={conn} />}
        {mode === 'agentic-ai' && (
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center', gap: '0.75rem',
          }}>
            <div style={{ fontSize: '2rem', color: C.dim, opacity: 0.4 }}>⊘</div>
            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.dim }}>
              Agentic AI — Not Yet Implemented
            </div>
            <p style={{ fontSize: '0.75rem', color: C.dim, textAlign: 'center', maxWidth: 360, lineHeight: 1.6 }}>
              Goal decomposition, task prioritization, and autonomous workflow
              management are reserved for a future build.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
