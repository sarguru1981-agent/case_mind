/**
 * AI Agent Investigation Console
 *
 * Handles all UI for AI Agent mode:
 *   Pre-run → Loading → Progressive ReAct Replay → Task Complete
 *
 * Concept taught:
 *   Tool Calling → Function Calling → ReAct Loop → Assigned Task Complete
 *
 * Data contract:
 *   All displayed content comes from real /api/agent/investigate responses.
 *   No hardcoded tool results. Marcus Vale visible only after financial observation.
 */
import { useState, useEffect, useRef } from 'react'
import { C } from '../tokens'
import MetricCard from './MetricCard'
import RelationshipGraph from './RelationshipGraph'

const BACKEND = 'http://localhost:8000'

const DEFAULT_TASK =
  'Using external investigative records, determine whether the dark blue Ford ' +
  'Transit and credential NF-3847 can be independently corroborated at the ' +
  'Kingsley Watch Co. on the night of MCR-2025-0291, identify the registered ' +
  'keeper of the vehicle, and determine whether any financial activity in the ' +
  'period following the Operation Nightfall incidents is consistent with ' +
  "Daniel Mercer's involvement."

// ── Tool display metadata ─────────────────────────────────────────────────────

const TOOL_META = {
  lookup_vehicle: {
    id:    'lookup_vehicle',
    title: 'Vehicle Records',
    sub:   'DVLA Registration Database',
    icon:  '⊡',
    color: C.blue,
  },
  query_access_logs: {
    id:    'query_access_logs',
    title: 'Access Logs',
    sub:   'Northstar Facilities Ltd',
    icon:  '⊕',
    color: C.orange,
  },
  query_surveillance: {
    id:    'query_surveillance',
    title: 'ANPR / Surveillance',
    sub:   'ANPR Network + CCTV',
    icon:  '◈',
    color: C.cyan,
  },
  query_financial_intelligence: {
    id:    'query_financial_intelligence',
    title: 'Financial Intelligence',
    sub:   'FIU — Operation Nightfall',
    icon:  '◆',
    color: C.green,
  },
}

const TOOL_ORDER = [
  'query_surveillance',
  'lookup_vehicle',
  'query_access_logs',
  'query_financial_intelligence',
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function getToolData(toolName, displayStep, agentState) {
  if (!agentState || displayStep === 0) return null
  const limit = Math.min(displayStep, agentState.tool_calls.length)
  for (let i = limit - 1; i >= 0; i--) {
    if (agentState.tool_calls[i].tool_name === toolName) {
      return { call: agentState.tool_calls[i], obs: agentState.observations[i] }
    }
  }
  return null
}

function formatArg(key, val) {
  if (key === '_call_id') return null
  return val
}

function ObservationSummary({ toolName, obs }) {
  if (!obs || obs.status !== 'success' || !obs.result) {
    if (obs?.status === 'not_found') {
      return <span style={{ color: C.muted, fontSize: '0.7rem' }}>No match found</span>
    }
    return null
  }
  const r = obs.result
  const lines = []

  if (toolName === 'query_surveillance') {
    const sightings = r.sightings || []
    const plates = sightings.filter(s => s.registration_captured).map(s => s.registration_plate)
    if (plates.length) lines.push({ label: 'Registration', value: plates[0], hi: true })
    const s = sightings[0]
    if (s) {
      lines.push({ label: 'Time', value: s.time_of_sighting })
      lines.push({ label: 'Confidence', value: s.confidence })
    }
  } else if (toolName === 'lookup_vehicle') {
    lines.push({ label: 'Keeper', value: r.registered_keeper, hi: true })
    lines.push({ label: 'Vehicle', value: `${r.colour} ${r.make} ${r.model}` })
  } else if (toolName === 'query_access_logs') {
    const events = r.access_events || []
    const oos = events.filter(e => e.access_type?.toLowerCase().includes('out-of-hours'))
    lines.push({ label: 'Events', value: `${events.length} recorded`, hi: events.length > 0 })
    if (oos.length > 0) lines.push({ label: 'Out-of-Hours', value: `${oos.length}  · no work order`, hi: true })
    lines.push({ label: 'Credential', value: r.credential_id })
  } else if (toolName === 'query_financial_intelligence') {
    const txns = r.transactions || []
    const transfers = r.inbound_transfers_from_mercer || []
    const cash = txns.filter(t => t.type === 'Cash Deposit').reduce((s, t) => s + t.amount_gbp, 0)
    const outTotal = txns.filter(t => t.type?.includes('Outbound')).reduce((s, t) => s + t.amount_gbp, 0)
    const recipients = [...new Set(txns.filter(t => t.recipient_name).map(t => t.recipient_name))]
    if (cash > 0) lines.push({ label: 'Cash Deposits', value: `£${cash.toLocaleString()}`, hi: true })
    if (outTotal > 0 && recipients.length > 0) lines.push({ label: 'Transfers to', value: recipients.join(', '), hi: true })
    if (transfers.length > 0) {
      const total = transfers.reduce((s, t) => s + t.amount_gbp, 0)
      lines.push({ label: 'Inbound (Mercer)', value: `£${total.toLocaleString()}`, hi: true })
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginTop: '0.35rem' }}>
      {lines.map(({ label, value, hi }) => (
        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.6rem', color: C.dim, textTransform: 'uppercase', letterSpacing: '0.08em', flexShrink: 0 }}>
            {label}
          </span>
          <span style={{ fontSize: '0.68rem', fontWeight: hi ? 700 : 400, color: hi ? C.white : C.muted, textAlign: 'right', fontFamily: hi ? 'monospace' : 'inherit' }}>
            {value}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── External Tool Card ────────────────────────────────────────────────────────

function ToolCard({ toolId, displayStep, agentState, isActive }) {
  const meta = TOOL_META[toolId]
  const data = getToolData(toolId, displayStep, agentState)
  const obs = data?.obs
  const call = data?.call

  let state = 'standby'
  if (data) {
    state = obs?.status === 'not_found' ? 'not_found'
          : obs?.status === 'success'   ? 'observed'
          : 'querying'
  }
  if (isActive && !data) state = 'querying'

  const stateColors = {
    standby:   { color: C.dim,    bg: 'transparent',  border: C.border,   dot: C.dim,    label: 'STANDBY'   },
    querying:  { color: meta.color, bg: meta.color + '10', border: meta.color + '50', dot: meta.color, label: 'QUERYING' },
    observed:  { color: C.green,  bg: C.greenBg,       border: C.greenBrd, dot: C.green,  label: 'OBSERVED'  },
    not_found: { color: C.muted,  bg: 'transparent',   border: C.border,   dot: C.muted,  label: 'NO MATCH'  },
  }
  const sc = stateColors[state]

  const args = call?.arguments
    ? Object.entries(call.arguments).filter(([k]) => k !== '_call_id')
    : null

  return (
    <div style={{
      background: sc.bg,
      border: `1px solid ${sc.border}`,
      borderLeft: `2px solid ${sc.dot}`,
      borderRadius: 5,
      padding: '0.55rem 0.7rem',
      transition: 'all 0.3s',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.15rem' }}>
            <span style={{ fontSize: '0.75rem', color: meta.color }}>{meta.icon}</span>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, color: C.text }}>{meta.title}</span>
          </div>
          <div style={{ fontSize: '0.55rem', color: C.dim, letterSpacing: '0.06em' }}>{meta.sub}</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
          <div style={{
            width: 5, height: 5, borderRadius: '50%', background: sc.dot,
            boxShadow: state === 'querying' ? `0 0 6px ${sc.dot}` : 'none',
            animation: state === 'querying' ? 'pulse-glow 1s ease-in-out infinite' : 'none',
          }} />
          <span style={{ fontSize: '0.5rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: sc.color }}>
            {sc.label}
          </span>
        </div>
      </div>

      {args && (
        <div style={{ marginTop: '0.4rem', padding: '0.3rem 0.5rem', background: C.bg, borderRadius: 3 }}>
          <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: C.dim, marginBottom: '0.2rem' }}>
            Query
          </div>
          {args.map(([k, v]) => (
            <div key={k} style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: meta.color, fontWeight: 700 }}>
              {v}
            </div>
          ))}
        </div>
      )}

      {state === 'observed' && <ObservationSummary toolName={toolId} obs={obs} />}
    </div>
  )
}

// ── Agent ReAct Flow Bar ──────────────────────────────────────────────────────

function AgentFlowBar({ displayStep, totalSteps, done }) {
  const stages = [
    { label: 'Assigned Task', done: displayStep > 0 || done, active: displayStep === 0 && !done },
    { label: 'Decide',        done: displayStep >= 1 || done, active: false },
    { label: 'Act',           done: displayStep >= 1 || done, active: false },
    { label: 'Observe',       done: displayStep >= 1 || done, active: false },
    { label: 'Decide Again',  done: displayStep >= 2 || done, active: false },
    { label: 'Act',           done: displayStep >= 2 || done, active: false },
    { label: 'Task Complete', done: done,                      active: false },
  ]

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`, borderRadius: 5,
      padding: '0.5rem 0.75rem',
    }}>
      <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.4rem' }}>
        Agent ReAct Loop
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', flexWrap: 'wrap' }}>
        {stages.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            {i > 0 && <span style={{ color: C.dim, fontSize: '0.6rem' }}>→</span>}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
              <div style={{
                width: 5, height: 5, borderRadius: '50%',
                background: s.done ? C.green : s.active ? C.cyan : C.dim,
                boxShadow: s.active ? `0 0 5px ${C.cyan}` : 'none',
              }} />
              <span style={{
                fontSize: '0.55rem', fontWeight: s.done ? 700 : 400,
                textTransform: 'uppercase', letterSpacing: '0.08em',
                color: s.done ? C.green : s.active ? C.cyan : C.dim,
              }}>
                {s.label}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── ReAct Iteration Card ──────────────────────────────────────────────────────

function IterationCard({ idx, toolCall, obs, isLast }) {
  const [expanded, setExpanded] = useState(false)
  const meta = TOOL_META[toolCall.tool_name] || { title: toolCall.tool_name, color: C.muted, icon: '⊡' }
  const args = Object.entries(toolCall.arguments).filter(([k]) => k !== '_call_id')

  return (
    <div
      className="anim-slide-in"
      style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderLeft: `2px solid ${meta.color}`, borderRadius: 5, overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        onClick={() => setExpanded(e => !e)}
        style={{
          padding: '0.5rem 0.7rem', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: '0.5rem',
        }}
      >
        <span style={{
          fontSize: '0.5rem', fontWeight: 700, color: meta.color,
          background: meta.color + '18', border: `1px solid ${meta.color + '35'}`,
          borderRadius: 3, padding: '0.12rem 0.4rem', letterSpacing: '0.08em',
          fontFamily: 'monospace', flexShrink: 0,
        }}>
          ITER {idx + 1}
        </span>
        <span style={{ fontSize: '0.65rem', color: meta.color }}>{meta.icon}</span>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: C.text, flex: 1 }}>
          {meta.title}
        </span>
        {args.slice(0, 1).map(([k, v]) => (
          <span key={k} style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: meta.color + 'cc' }}>
            {String(v).slice(0, 20)}
          </span>
        ))}
        <span style={{ fontSize: '0.6rem', color: C.dim }}>{expanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div style={{ padding: '0 0.7rem 0.6rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
          {/* Decision */}
          <div style={{ padding: '0.4rem 0.6rem', background: C.bg, borderRadius: 4 }}>
            <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.12em', color: C.dim, marginBottom: '0.2rem' }}>
              Decision
            </div>
            <p style={{ fontSize: '0.68rem', color: C.muted, lineHeight: 1.55 }}>
              {obs?.query_summary || `Calling ${meta.title}`}
            </p>
          </div>

          {/* Function Call */}
          <div style={{ padding: '0.4rem 0.6rem', background: C.bg, borderRadius: 4, border: `1px solid ${meta.color + '25'}` }}>
            <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.12em', color: meta.color, marginBottom: '0.25rem' }}>
              Function Call · {toolCall.tool_name}
            </div>
            {args.map(([k, v]) => (
              <div key={k} style={{ display: 'flex', gap: '0.5rem', alignItems: 'baseline' }}>
                <span style={{ fontSize: '0.6rem', color: C.dim, fontFamily: 'monospace', flexShrink: 0 }}>{k}</span>
                <span style={{ fontSize: '0.7rem', color: meta.color, fontFamily: 'monospace', fontWeight: 700 }}>{String(v)}</span>
              </div>
            ))}
          </div>

          {/* Observation */}
          {obs && (
            <div style={{
              padding: '0.4rem 0.6rem', background: C.bg, borderRadius: 4,
              border: `1px solid ${obs.status === 'success' ? C.greenBrd : C.border}`,
            }}>
              <div style={{
                fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.12em',
                color: obs.status === 'success' ? C.green : C.muted, marginBottom: '0.2rem',
              }}>
                Observation · {obs.status}
              </div>
              <div style={{ fontSize: '0.65rem', color: C.muted, fontFamily: 'monospace' }}>
                {obs.query_summary}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Agent Pre-Run State ───────────────────────────────────────────────────────

function AgentPreRunState({ task, setTask, onRun, loading, conn }) {
  const canRun = task.trim().length >= 10 && !loading && conn !== 'disconnected'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2.5rem 1.5rem' }}>
      <div style={{ width: '100%', maxWidth: 700 }}>

        {/* Header card */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderTop: `2px solid ${C.blue}`,
          borderRadius: 6, padding: '1.25rem 1.5rem', marginBottom: '1.25rem',
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '50%',
            background: `radial-gradient(ellipse at 30% 0%, ${C.blueBg} 0%, transparent 70%)`,
            pointerEvents: 'none',
          }} />
          <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.18em', color: C.blue, marginBottom: '0.75rem' }}>
            AI Agent · Operation Nightfall
          </div>
          <h1 style={{
            fontSize: '1.9rem', fontWeight: 800, color: C.white,
            lineHeight: 1.15, letterSpacing: '-0.025em', marginBottom: '0.65rem',
          }}>
            Tools called.<br />
            Results observed.<br />
            <span style={{ color: C.blue }}>Task complete.</span>
          </h1>
          <p style={{ fontSize: '0.84rem', color: C.muted, lineHeight: 1.65, marginBottom: '1rem' }}>
            Build 3 — Stage 2. The AI Agent receives an Assigned Task and
            determines how to investigate by calling external tools: ANPR /
            Surveillance, Vehicle Records, Access Logs, and Financial Intelligence.
          </p>

          {/* ReAct flow preview */}
          <div style={{ padding: '0.7rem 0.85rem', background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4 }}>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.45rem' }}>
              ReAct Loop
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              {['Assigned Task', 'Decide', 'Act', 'Observe', 'Decide Again', 'Act', 'Task Complete'].map((s, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  {i > 0 && <span style={{ color: C.dim, fontSize: '0.65rem' }}>→</span>}
                  <span style={{
                    fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.08em',
                    color: s === 'Task Complete' ? C.green : s === 'Assigned Task' ? C.blue : C.muted,
                    fontWeight: (s === 'Task Complete' || s === 'Assigned Task') ? 700 : 400,
                  }}>
                    {s}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* External systems preview */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '0.85rem 1.25rem', marginBottom: '1.25rem',
        }}>
          <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.6rem' }}>
            External Investigative Systems — Ready
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            {TOOL_ORDER.map(id => {
              const m = TOOL_META[id]
              return (
                <div key={id} style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.4rem 0.6rem',
                  background: C.bg, border: `1px solid ${C.border}`, borderLeft: `2px solid ${m.color}`,
                  borderRadius: 4,
                }}>
                  <span style={{ fontSize: '0.75rem', color: m.color }}>{m.icon}</span>
                  <div>
                    <div style={{ fontSize: '0.62rem', fontWeight: 700, color: C.text }}>{m.title}</div>
                    <div style={{ fontSize: '0.52rem', color: C.dim }}>{m.sub}</div>
                  </div>
                  <span style={{ marginLeft: 'auto', fontSize: '0.48rem', color: C.dim, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    STANDBY
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Task form */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
        }}>
          <div>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.4rem' }}>
              Assigned Investigation Task
            </div>
            <textarea
              value={task}
              onChange={e => setTask(e.target.value)}
              style={{
                width: '100%', background: C.bg, border: `1px solid ${C.borderHi}`,
                borderRadius: 5, padding: '0.7rem 1rem', color: C.text,
                fontSize: '0.875rem', outline: 'none', resize: 'vertical',
                minHeight: 92, fontFamily: 'inherit', lineHeight: 1.55,
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={onRun}
              disabled={!canRun}
              style={{
                background: canRun ? C.btn : C.border,
                color: canRun ? C.white : C.dim,
                border: `1px solid ${canRun ? C.btn + 'aa' : C.border}`,
                borderRadius: 5, padding: '0.6rem 1.75rem',
                fontSize: '0.875rem', fontWeight: 700,
                cursor: canRun ? 'pointer' : 'not-allowed',
                letterSpacing: '0.02em', transition: 'all 0.15s',
                boxShadow: canRun ? `0 0 12px ${C.btn}40` : 'none',
              }}
            >
              Run Agent Investigation
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

// ── Agent Loading State ───────────────────────────────────────────────────────

function AgentLoadingState() {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: '1.5rem', padding: '3rem 2rem',
    }}>
      <svg width={160} height={160} viewBox="0 0 160 160">
        {[55, 40, 25].map((r, i) => (
          <circle key={r} cx={80} cy={80} r={r}
            fill="none"
            stroke={i === 0 ? C.blue : i === 1 ? C.cyan : C.blue}
            strokeWidth={i === 1 ? 1.5 : 1}
            opacity={i === 1 ? 0.6 : 0.3}
            strokeDasharray={i === 0 ? '6,4' : i === 2 ? '2,3' : undefined}
            style={{ animation: `pulse-glow ${1.5 + i * 0.4}s ease-in-out infinite` }}
          />
        ))}
        <text x={80} y={75} textAnchor="middle" fill={C.blue} fontSize="10" fontFamily="monospace" fontWeight="700">AGENT</text>
        <text x={80} y={89} textAnchor="middle" fill={C.blue} fontSize="10" fontFamily="monospace" fontWeight="700">RUNNING</text>
      </svg>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.blue, marginBottom: '0.5rem' }}>
          ReAct Loop Executing
        </div>
        <p style={{ fontSize: '0.875rem', color: C.muted, lineHeight: 1.6 }}>
          Agent is reasoning over external tool observations…
        </p>
      </div>
    </div>
  )
}

// ── Left Column — Agent Overview ──────────────────────────────────────────────

function AgentOverview({ agentState, displayStep, done, task, conn }) {
  const totalCalls = agentState?.tool_calls?.length ?? 0
  const activeToolId = (agentState && displayStep > 0 && displayStep <= totalCalls)
    ? agentState.tool_calls[displayStep - 1]?.tool_name
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {/* Operation card */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderTop: `2px solid ${C.blue}`,
        borderRadius: 6, padding: '0.75rem 0.85rem', position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: `radial-gradient(ellipse at 50% 0%, ${C.blueBg} 0%, transparent 70%)`,
          pointerEvents: 'none',
        }} />
        <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.18em', color: C.blue + '99', marginBottom: '0.3rem' }}>
          AI Agent · Active Operation
        </div>
        <div style={{ fontSize: '0.9rem', fontWeight: 800, color: C.white, letterSpacing: '0.04em', marginBottom: '0.15rem' }}>
          OPERATION NIGHTFALL
        </div>
        <div style={{ fontSize: '0.7rem', color: C.muted, marginBottom: '0.6rem' }}>
          External Tool Investigation
        </div>
        {done ? (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.3rem 0.6rem', background: C.greenBg, border: `1px solid ${C.greenBrd}`, borderRadius: 3,
          }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: C.green, boxShadow: `0 0 6px ${C.green}` }} />
            <span style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: C.green }}>
              Assigned Task Complete
            </span>
          </div>
        ) : agentState ? (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.3rem 0.6rem', background: C.blueBg, border: `1px solid ${C.blueBrd}`, borderRadius: 3,
          }}>
            <div style={{
              width: 7, height: 7, borderRadius: '50%', background: C.blue,
              animation: 'pulse-glow 1s ease-in-out infinite',
            }} />
            <span style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: C.blue }}>
              Replaying Trace…
            </span>
          </div>
        ) : null}
      </div>

      {/* Assigned task */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: '0.65rem 0.85rem' }}>
        <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.35rem' }}>
          Assigned Investigation Task
        </div>
        <p style={{ fontSize: '0.72rem', color: C.text, lineHeight: 1.55 }}>
          {task}
        </p>
      </div>

      {/* ReAct flow */}
      <AgentFlowBar displayStep={displayStep} totalSteps={agentState?.tool_calls?.length ?? 0} done={done} />

      {/* External system tool cards */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
        <div style={{
          padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
          fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
        }}>
          External Investigative Systems
        </div>
        <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          {TOOL_ORDER.map(id => (
            <ToolCard
              key={id}
              toolId={id}
              displayStep={displayStep}
              agentState={agentState}
              isActive={activeToolId === id}
            />
          ))}
        </div>
      </div>

      {/* Backend status */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: 6, padding: '0.5rem 0.85rem',
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

// ── Evidence Panel ────────────────────────────────────────────────────────────

function EvidencePanel({ agentState, displayStep, onReset }) {
  const visibleObs = agentState?.observations.slice(0, displayStep) ?? []
  const visibleEvidence = agentState?.evidence.filter(ev => {
    const callIdx = agentState.tool_calls.findIndex(tc => tc.call_id === ev.call_id)
    return callIdx !== -1 && callIdx < displayStep
  }) ?? []

  const done = displayStep >= (agentState?.tool_calls?.length ?? 0) && !!agentState

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {/* Evidence items */}
      {visibleEvidence.length > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          <div style={{
            padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Evidence — {visibleEvidence.length} confirmed fact{visibleEvidence.length !== 1 ? 's' : ''}
          </div>
          <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {visibleEvidence.map((ev, i) => {
              const color = ev.confidence === 'HIGH' ? C.green : ev.confidence === 'MEDIUM' ? C.orange : C.muted
              return (
                <div key={i} className="anim-slide-in" style={{
                  padding: '0.45rem 0.6rem',
                  background: color + '0a', border: `1px solid ${color + '30'}`,
                  borderLeft: `2px solid ${color}`, borderRadius: 4,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                    <span style={{
                      fontSize: '0.48rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
                      color, background: color + '18', borderRadius: 2, padding: '0.08rem 0.35rem',
                    }}>
                      {ev.confidence}
                    </span>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.48rem', color: C.dim }}>
                      {ev.source_tool.replace('query_', '').replace('lookup_', '')}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.7rem', color: C.text, lineHeight: 1.5 }}>{ev.fact}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ReAct iterations */}
      {agentState && displayStep > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          <div style={{
            padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
              ReAct Iterations · {displayStep} of {agentState.tool_calls.length}
            </span>
          </div>
          <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {agentState.tool_calls.slice(0, displayStep).map((tc, i) => (
              <IterationCard
                key={tc.call_id}
                idx={i}
                toolCall={tc}
                obs={agentState.observations[i]}
                isLast={i === displayStep - 1}
              />
            ))}
          </div>
        </div>
      )}

      {/* Task complete */}
      {done && (
        <div className="anim-slide-in" style={{
          background: C.greenBg, border: `1px solid ${C.greenBrd}`,
          borderRadius: 6, padding: '0.85rem 1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <div style={{ width: 9, height: 9, borderRadius: '50%', background: C.green, boxShadow: `0 0 8px ${C.green}` }} />
            <span style={{ fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: C.green }}>
              Assigned Task Complete
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', marginBottom: '0.6rem' }}>
            {[
              agentState.tool_calls.some(t => t.tool_name === 'query_surveillance') && 'Vehicle corroborated at scene',
              agentState.tool_calls.some(t => t.tool_name === 'lookup_vehicle')     && 'Registered keeper identified',
              agentState.tool_calls.some(t => t.tool_name === 'query_access_logs')  && 'Credential access corroborated',
              agentState.tool_calls.some(t => t.tool_name === 'query_financial_intelligence') && 'Financial anomaly identified',
              agentState.evidence.some(e => e.fact.includes('Marcus Vale')) && 'New financial connection discovered',
            ].filter(Boolean).map((finding, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ color: C.green, fontSize: '0.65rem' }}>✓</span>
                <span style={{ fontSize: '0.7rem', color: C.text }}>{finding}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => alert(agentState.completion_summary)}
              style={{
                flex: 1, background: C.greenBg, color: C.green,
                border: `1px solid ${C.greenBrd}`, borderRadius: 4,
                padding: '0.4rem 0.75rem', fontSize: '0.62rem', fontWeight: 700,
                cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '0.06em',
              }}
            >
              View Full Agent Summary
            </button>
            <button
              onClick={onReset}
              style={{
                background: 'transparent', border: `1px solid ${C.border}`,
                borderRadius: 4, padding: '0.4rem 0.75rem',
                fontSize: '0.62rem', color: C.muted, cursor: 'pointer',
                letterSpacing: '0.06em', textTransform: 'uppercase',
              }}
            >
              New Task
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Build agent nodes for graph ───────────────────────────────────────────────

function buildAgentNodes(agentState, displayStep) {
  if (!agentState || displayStep === 0) return { agentNodes: [], agentEdges: [] }

  const agentNodes = []
  const agentEdges = []
  const visibleCalls = agentState.tool_calls.slice(0, displayStep)
  const visibleObs   = agentState.observations.slice(0, displayStep)

  for (let i = 0; i < visibleCalls.length; i++) {
    const tc  = visibleCalls[i]
    const obs = visibleObs[i]
    if (!obs || obs.status !== 'success' || !obs.result) continue

    if (tc.tool_name === 'query_surveillance') {
      const sightings = obs.result.sightings || []
      for (const s of sightings) {
        if (s.registration_captured && s.registration_plate) {
          if (!agentNodes.find(n => n.id === s.registration_plate)) {
            agentNodes.push({
              id: s.registration_plate, label: s.registration_plate,
              type: 'VEHICLE', color: C.blue,
              x: 535, y: 320, isNew: true,
            })
            agentEdges.push({ from: 'robbery-004', to: s.registration_plate, label: 'sighted', isNew: true })
          }
        }
      }
    }

    if (tc.tool_name === 'lookup_vehicle') {
      const keeper = obs.result.registered_keeper
      const reg    = obs.result.registration || tc.arguments.registration
      if (keeper) {
        const nodeId = 'ext_keeper_' + keeper.toLowerCase().replace(/\s+/g, '_')
        if (!agentNodes.find(n => n.id === nodeId)) {
          agentNodes.push({
            id: nodeId, label: keeper,
            type: 'PERSON', color: C.yellow,
            x: 535, y: 170, isNew: true,
          })
          if (reg && agentNodes.find(n => n.id === reg)) {
            agentEdges.push({ from: reg, to: nodeId, label: 'keeper', isNew: true })
          }
        }
      }
    }

    if (tc.tool_name === 'query_access_logs') {
      const cred   = obs.result.credential_id
      const person = obs.result.assigned_to
      const events = obs.result.access_events || []
      const oos    = events.filter(e => e.access_type?.toLowerCase().includes('out-of-hours'))
      if (cred) {
        if (!agentNodes.find(n => n.id === cred)) {
          agentNodes.push({
            id: cred, label: cred,
            type: 'CREDENTIAL', color: C.red,
            x: 400, y: 340, isNew: true,
          })
          agentEdges.push({ from: 'robbery-004', to: cred, label: 'access', isNew: true })
        }
        const personNodeId = 'ext_keeper_' + (person || '').toLowerCase().replace(/\s+/g, '_')
        const personNode = agentNodes.find(n => n.id === personNodeId)
        if (personNode) {
          agentEdges.push({ from: personNodeId, to: cred, label: 'holds', isNew: true })
        }
      }
    }

    if (tc.tool_name === 'query_financial_intelligence') {
      const txns      = obs.result.transactions || []
      const transfers = obs.result.inbound_transfers_from_mercer || []
      const recipients = [...new Set(txns.filter(t => t.recipient_name).map(t => t.recipient_name))]
      const subjectName = obs.result.name

      for (const recipient of recipients) {
        const recipId = 'ext_' + recipient.toLowerCase().replace(/\s+/g, '_')
        if (!agentNodes.find(n => n.id === recipId)) {
          agentNodes.push({
            id: recipId, label: recipient,
            type: 'PERSON', color: C.orange,
            x: 670, y: 195, isNew: true,
          })
          const subjectId = 'ext_keeper_' + (subjectName || '').toLowerCase().replace(/\s+/g, '_')
          agentEdges.push({ from: subjectId, to: recipId, label: '£ transfer', isNew: true })
        }
      }
    }
  }

  return { agentNodes, agentEdges }
}

// ── Main Agent Workstation ────────────────────────────────────────────────────

function AgentWorkstation({ agentState, task, conn, onReset, displayStep, done, selectedNodeId, onNodeSelect }) {
  const { agentNodes, agentEdges } = buildAgentNodes(agentState, displayStep)
  const totalCalls = agentState?.tool_calls?.length ?? 0

  const metrics = [
    { label: 'Iterations',   value: agentState.iteration,                     color: C.blue,   icon: '↻', sub: 'react loops' },
    { label: 'Tool Calls',   value: Math.min(displayStep, totalCalls),         color: C.cyan,   icon: '⊕', sub: 'dispatched' },
    { label: 'Observations', value: Math.min(displayStep, totalCalls),         color: C.orange, icon: '◈', sub: 'recorded' },
    { label: 'Evidence',     value: agentState.evidence.filter(e => {
      const idx = agentState.tool_calls.findIndex(tc => tc.call_id === e.call_id)
      return idx !== -1 && idx < displayStep
    }).length,                                                                  color: C.green,  icon: '●', sub: 'confirmed facts' },
    { label: 'Status',       value: done ? '✓' : '…',                          color: done ? C.green : C.blue, icon: done ? '✓' : '…', sub: done ? 'complete' : 'running' },
  ]

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      {/* Workstation header */}
      <div style={{
        padding: '0.55rem 1rem', borderBottom: `1px solid ${C.border}`,
        background: C.panel, display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: done ? C.green : C.blue,
            boxShadow: `0 0 6px ${done ? C.green : C.blue}`,
            animation: done ? 'none' : 'pulse-glow 1s ease-in-out infinite',
          }} />
          <span style={{
            fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em',
            color: done ? C.green : C.blue,
          }}>
            {done ? 'Assigned Task Complete' : `Agent Running · ${displayStep}/${totalCalls} iterations`}
          </span>
        </div>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
          {['Assigned Task', '→', 'Decide', '→', 'Act', '→', 'Observe', '→', 'Task Complete'].map((item, i) => (
            item === '→'
              ? <span key={i} style={{ color: C.dim, fontSize: '0.6rem' }}>→</span>
              : <span key={i} style={{ fontSize: '0.55rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: done ? C.green : C.blue }}>{item}</span>
          ))}
        </div>
      </div>

      {/* 3-col workspace */}
      <div className="investigation-workspace anim-slide-in">
        {/* Left col */}
        <AgentOverview agentState={agentState} displayStep={displayStep} done={done} task={task} conn={conn} />

        {/* Center col */}
        <div className="ws-col">
          <div className="metrics-row">
            {metrics.map(m => <MetricCard key={m.label} label={m.label} value={m.value} color={m.color} icon={m.icon} sub={m.sub} />)}
          </div>
          <RelationshipGraph
            result={null}
            agentNodes={agentNodes}
            agentEdges={agentEdges}
            selectedNodeId={selectedNodeId}
            onNodeSelect={onNodeSelect}
          />
        </div>

        {/* Right col */}
        <div className="ws-col">
          <EvidencePanel agentState={agentState} displayStep={displayStep} onReset={onReset} />
        </div>
      </div>
    </div>
  )
}

// ── Root export ───────────────────────────────────────────────────────────────

export default function AgentInvestigationConsole({ conn }) {
  const [task, setTask]               = useState(DEFAULT_TASK)
  const [loading, setLoading]         = useState(false)
  const [agentState, setAgentState]   = useState(null)
  const [displayStep, setDisplayStep] = useState(0)
  const [error, setError]             = useState(null)
  const [selectedNodeId, setSelectedNodeId] = useState(null)

  const done = agentState !== null && displayStep >= agentState.tool_calls.length

  // Progressive replay — one iteration every 700ms
  useEffect(() => {
    if (!agentState) return
    if (displayStep >= agentState.tool_calls.length) return
    const t = setTimeout(() => setDisplayStep(s => s + 1), 700)
    return () => clearTimeout(t)
  }, [agentState, displayStep])

  const run = async () => {
    if (!task.trim() || loading) return
    setLoading(true); setAgentState(null); setDisplayStep(0); setError(null); setSelectedNodeId(null)
    try {
      const res = await fetch(`${BACKEND}/api/agent/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assigned_task: task.trim() }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        setError(`HTTP ${res.status}: ${err.detail || res.statusText}`)
      } else {
        setAgentState(await res.json())
        setDisplayStep(0)
      }
    } catch (e) {
      setError(`Network error: ${String(e)}`)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => { setAgentState(null); setDisplayStep(0); setError(null); setSelectedNodeId(null) }

  if (loading) return <AgentLoadingState />

  if (!agentState) {
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
        <AgentPreRunState task={task} setTask={setTask} onRun={run} loading={loading} conn={conn} />
      </>
    )
  }

  return (
    <AgentWorkstation
      agentState={agentState}
      task={task}
      conn={conn}
      onReset={reset}
      displayStep={displayStep}
      done={done}
      selectedNodeId={selectedNodeId}
      onNodeSelect={setSelectedNodeId}
    />
  )
}
