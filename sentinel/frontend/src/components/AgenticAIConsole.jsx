/**
 * Agentic AI Investigation Console
 *
 * Handles the UI for Agentic AI mode:
 *   Pre-run → Loading → 3-col Mission Workstation → READY FOR HUMAN REVIEW
 *
 * Concept taught:
 *   Mission → Goal Decomposition → Task Prioritization →
 *   Capability Routing → Execute → Adapt → Create New Tasks →
 *   Reassess → Continue → Human Review
 *
 * Data contract:
 *   All displayed content comes from real /api/agentic-ai/mission responses.
 *   MBK-4172 absent before surveillance returns it.
 *   Marcus Vale absent before financial returns it.
 *   Final status is always READY_FOR_HUMAN_REVIEW — never CASE_SOLVED.
 */
import { useState } from 'react'
import { C } from '../tokens'
import MetricCard from './MetricCard'
import RelationshipGraph from './RelationshipGraph'

const BACKEND = 'http://localhost:8000'

const BROAD_MISSION =
  'Investigate the Operation Nightfall robbery series, determine whether the' +
  ' four incidents are connected, identify the strongest persons of interest,' +
  ' evaluate significant alternative leads, and produce an evidence-backed' +
  ' investigation assessment for human review.'

// ── Priority & status metadata ────────────────────────────────────────────────

const PRIORITY_COLOR = {
  CRITICAL: C.red,
  HIGH:     C.orange,
  MEDIUM:   C.cyan,
  LOW:      C.dim,
}

const STATUS_COLOR = {
  COMPLETED:      C.green,
  IN_PROGRESS:    C.cyan,
  READY:          C.blue,
  BLOCKED:        C.dim,
  DEPRIORITIZED:  C.dim,
  NOT_STARTED:    C.dim,
}

const CAPABILITY_COLOR = {
  agentic_rag: C.cyan,
  ai_agent:    C.blue,
  synthesis:   C.orange,
}

const CAPABILITY_LABEL = {
  agentic_rag: 'Agentic RAG',
  ai_agent:    'AI Agent',
  synthesis:   'Synthesis',
}

const WORKFLOW_EVENT_META = {
  MISSION_RECEIVED:              { color: C.green,  icon: '▶', label: 'Mission Received' },
  MISSION_DECOMPOSED:            { color: C.cyan,   icon: '◈', label: 'Goal Decomposed' },
  TASK_CREATED:                  { color: C.blue,   icon: '+', label: 'Task Created' },
  TASK_CREATED_FROM_FINDING:     { color: C.orange, icon: '◆', label: 'Task from Finding' },
  TASK_PRIORITIZED:              { color: C.cyan,   icon: '↑', label: 'Prioritized' },
  TASK_STARTED:                  { color: C.cyan,   icon: '→', label: 'Task Started' },
  CAPABILITY_SELECTED:           { color: C.blue,   icon: '⊕', label: 'Capability' },
  TASK_COMPLETED:                { color: C.green,  icon: '✓', label: 'Task Complete' },
  NEW_FINDING:                   { color: C.orange, icon: '●', label: 'New Finding' },
  TASK_REPRIORITIZED:            { color: C.orange, icon: '↑', label: 'Reprioritized' },
  TASK_DEPRIORITIZED:            { color: C.dim,    icon: '↓', label: 'Deprioritized' },
  WORKFLOW_REASSESSED:           { color: C.orange, icon: '⊙', label: 'Workflow Reassessed' },
  MISSION_READY_FOR_HUMAN_REVIEW:{ color: C.green,  icon: '★', label: 'Ready for Review' },
}

// ── Mission concept flow bar ──────────────────────────────────────────────────

function MissionFlowBadge({ label, active, complete }) {
  const color = complete ? C.green : active ? C.green : C.dim
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

function MissionFlow({ running, result }) {
  const done = !!result
  const stages = [
    'Mission', 'Decompose', 'Prioritize', 'Execute', 'Reassess', 'Create', 'Continue', 'Human Review',
  ]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', padding: '0.4rem 0' }}>
      {stages.map((s, i) => (
        <span key={s} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <MissionFlowBadge label={s} active={running} complete={done} />
          {i < stages.length - 1 && <FlowArrow />}
        </span>
      ))}
    </div>
  )
}

// ── Pre-run state ─────────────────────────────────────────────────────────────

function AgenticAIPreRunState({ mission, setMission, maxCycles, setMaxCycles, onRun, loading, conn }) {
  const canRun = mission.trim().length >= 10 && !loading && conn !== 'disconnected'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2.5rem 1.5rem' }}>
      <div style={{ width: '100%', maxWidth: 700 }}>

        {/* Hero card */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderTop: `2px solid ${C.green}`,
          borderRadius: 6, padding: '1.25rem 1.5rem', marginBottom: '1.25rem',
          position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: '50%',
            background: `radial-gradient(ellipse at 30% 0%, ${C.greenBg} 0%, transparent 70%)`,
            pointerEvents: 'none',
          }} />
          <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.18em', color: C.green, marginBottom: '0.75rem' }}>
            Agentic AI · Operation Nightfall
          </div>
          <h1 style={{
            fontSize: '1.9rem', fontWeight: 800, color: C.white,
            lineHeight: 1.15, letterSpacing: '-0.025em', marginBottom: '0.65rem',
          }}>
            A mission with<br />
            its own agenda,<br />
            <span style={{ color: C.green }}>not yours.</span>
          </h1>
          <p style={{ fontSize: '0.84rem', color: C.muted, lineHeight: 1.65, marginBottom: '1rem' }}>
            Build 4 — A broad investigation mission is decomposed into prioritised tasks.
            The orchestrator selects the right capability for each task, adapts as new
            evidence emerges, creates follow-up tasks, and delivers a human-ready
            assessment — without you issuing a single query.
          </p>
          <div style={{ padding: '0.7rem 0.85rem', background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4 }}>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.45rem' }}>
              Mission Orchestration Loop
            </div>
            <MissionFlow running={false} result={null} />
          </div>
        </div>

        {/* Capability routing */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '0.85rem 1.25rem', marginBottom: '1.25rem',
        }}>
          <div style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.12em', color: C.muted, marginBottom: '0.65rem' }}>
            Capability Routing — Orchestrator selects automatically
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <div style={{
              padding: '0.35rem 0.85rem',
              background: C.greenBg, border: `1px solid ${C.greenBrd}`,
              borderRadius: 4, fontSize: '0.62rem', fontWeight: 700,
              color: C.green, textTransform: 'uppercase', letterSpacing: '0.08em',
            }}>
              Agentic AI
            </div>
            <span style={{ color: C.dim, fontSize: '0.7rem' }}>→</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[
                { label: 'Agentic RAG', color: C.cyan, bg: C.cyanBg, brd: C.cyanBrd, sub: 'Archive search' },
                { label: 'AI Agent',    color: C.blue, bg: C.blueBg, brd: C.blueBrd, sub: 'External tools' },
                { label: 'Synthesis',   color: C.orange, bg: C.orangeBg, brd: C.orangeBrd, sub: 'LLM assessment' },
              ].map(cap => (
                <div key={cap.label} style={{
                  padding: '0.35rem 0.75rem',
                  background: cap.bg, border: `1px solid ${cap.brd}`,
                  borderRadius: 4, textAlign: 'center',
                }}>
                  <div style={{ fontSize: '0.6rem', fontWeight: 700, color: cap.color, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {cap.label}
                  </div>
                  <div style={{ fontSize: '0.5rem', color: C.dim, marginTop: '0.1rem' }}>{cap.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Mission form */}
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
          padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.75rem',
        }}>
          <div>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.4rem' }}>
              Investigation Mission
            </div>
            <textarea
              value={mission}
              onChange={e => setMission(e.target.value)}
              style={{
                width: '100%', background: C.bg, border: `1px solid ${C.borderHi}`,
                borderRadius: 5, padding: '0.7rem 1rem', color: C.text,
                fontSize: '0.875rem', outline: 'none', resize: 'vertical',
                minHeight: 100, fontFamily: 'inherit', lineHeight: 1.55,
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <label style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
                Max Cycles
              </label>
              <input
                type="number" min={1} max={30} value={maxCycles}
                onChange={e => setMaxCycles(Math.max(1, Math.min(30, parseInt(e.target.value, 10) || 15)))}
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
                background: canRun ? C.green : C.border,
                color: canRun ? C.bg : C.dim,
                border: `1px solid ${canRun ? C.green + 'aa' : C.border}`,
                borderRadius: 5, padding: '0.6rem 1.75rem',
                fontSize: '0.875rem', fontWeight: 700,
                cursor: canRun ? 'pointer' : 'not-allowed',
                letterSpacing: '0.04em', transition: 'all 0.15s',
                boxShadow: canRun ? `0 0 14px ${C.green}40` : 'none',
                textTransform: 'uppercase',
              }}
            >
              Start Mission
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

// ── Loading state ─────────────────────────────────────────────────────────────

function AgenticAILoadingState() {
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
            stroke={i === 0 ? C.green : i === 1 ? C.cyan : C.green}
            strokeWidth={i === 1 ? 1.5 : 1}
            opacity={i === 1 ? 0.6 : 0.3}
            strokeDasharray={i === 0 ? '6,4' : i === 2 ? '2,3' : undefined}
            style={{ animation: `pulse-glow ${1.5 + i * 0.4}s ease-in-out infinite` }}
          />
        ))}
        <text x={90} y={85} textAnchor="middle" fill={C.green} fontSize="9.5" fontFamily="monospace" fontWeight="700">
          MISSION
        </text>
        <text x={90} y={99} textAnchor="middle" fill={C.green} fontSize="9.5" fontFamily="monospace" fontWeight="700">
          ACTIVE
        </text>
        {[
          { cx: 28, cy: 28,  label: 'ARCHIVE', color: C.cyan },
          { cx: 152, cy: 28, label: 'AGENT',   color: C.blue },
          { cx: 28, cy: 152, label: 'SYNTH',   color: C.orange },
          { cx: 152, cy: 152,label: 'REVIEW',  color: C.green },
        ].map(({ cx, cy, label, color }) => (
          <g key={label}>
            <line x1={cx} y1={cy} x2={90} y2={90}
              stroke={color + '40'} strokeWidth={1} strokeDasharray="3,3"
              style={{ animation: 'dash-flow 1.5s linear infinite' }}
            />
            <circle cx={cx} cy={cy} r={16} fill={C.surface} stroke={color} strokeWidth={1}
              style={{ animation: 'pulse-glow 2s ease-in-out infinite' }}
            />
            <text x={cx} y={cy + 3.5} textAnchor="middle" fill={color} fontSize="5.5" fontFamily="monospace" fontWeight="700">
              {label}
            </text>
          </g>
        ))}
      </svg>

      <div style={{ textAlign: 'center', maxWidth: 480 }}>
        <div style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.green, marginBottom: '0.5rem' }}>
          Mission In Progress
        </div>
        <p style={{ fontSize: '0.875rem', color: C.muted, lineHeight: 1.6, marginBottom: '1rem' }}>
          Decomposing goal → prioritising tasks → routing to capabilities → adapting workflow…
        </p>
        <MissionFlow running={true} result={null} />
      </div>
    </div>
  )
}

// ── Workstation components ────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const isReady = status === 'READY_FOR_HUMAN_REVIEW'
  const isMax   = status === 'MAX_CYCLES_REACHED'
  const color   = isReady ? C.green : isMax ? C.orange : C.cyan
  const bg      = isReady ? C.greenBg : isMax ? C.orangeBg : C.cyanBg
  const brd     = isReady ? C.greenBrd : isMax ? C.orangeBrd : C.cyanBrd
  const label   = isReady ? '★ READY FOR HUMAN REVIEW'
                : isMax   ? '⊙ MAX CYCLES REACHED'
                :           status
  return (
    <div style={{
      background: bg, border: `1px solid ${brd}`, borderRadius: 4,
      padding: '0.2rem 0.6rem',
      fontSize: '0.55rem', fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '0.1em', color,
      boxShadow: isReady ? `0 0 10px ${C.green}40` : 'none',
    }}>
      {label}
    </div>
  )
}

function MissionControl({ state }) {
  const completedTasks  = state.tasks.filter(t => t.status === 'COMPLETED').length
  const criticalHighOpen = state.tasks.filter(t =>
    (t.priority === 'CRITICAL' || t.priority === 'HIGH') &&
    !['COMPLETED', 'DEPRIORITIZED'].includes(t.status)
  ).length

  return (
    <div className="ws-col">
      {/* Mission header */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderTop: `2px solid ${C.green}`,
        borderRadius: 6, padding: '0.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.65rem',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
          background: `radial-gradient(ellipse at 50% 0%, ${C.greenBg} 0%, transparent 70%)`,
          pointerEvents: 'none',
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.2rem' }}>
              Operation
            </div>
            <div style={{ fontSize: '0.72rem', fontWeight: 800, color: C.green, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Operation Nightfall
            </div>
          </div>
          <StatusBadge status={state.status} />
        </div>

        <div>
          <div style={{ fontSize: '0.48rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.dim, marginBottom: '0.3rem' }}>
            Mission Statement
          </div>
          <p style={{ fontSize: '0.7rem', color: C.muted, lineHeight: 1.55 }}>
            {state.mission}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.65rem' }}>
          {[
            { label: 'Cycles', value: state.cycle_count, color: C.green },
            { label: 'Reassess', value: state.reassessment_count, color: C.orange },
            { label: 'Completed', value: completedTasks, color: C.cyan },
            { label: 'Open C/H', value: criticalHighOpen, color: criticalHighOpen > 0 ? C.orange : C.green },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              flex: 1, background: C.bg, border: `1px solid ${C.border}`, borderRadius: 4,
              padding: '0.4rem 0.5rem', textAlign: 'center',
            }}>
              <div style={{ fontFamily: 'monospace', fontSize: '1.1rem', fontWeight: 800, color, lineHeight: 1 }}>
                {value}
              </div>
              <div style={{ fontSize: '0.47rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: C.dim, marginTop: '0.2rem' }}>
                {label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Completion criteria */}
      {state.completion_criteria?.length > 0 && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Completion Criteria
          </div>
          <div style={{ padding: '0.6rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {state.completion_criteria.map((criterion, i) => {
              const done = state.status === 'READY_FOR_HUMAN_REVIEW'
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.4rem' }}>
                  <span style={{ color: done ? C.green : C.dim, fontSize: '0.65rem', flexShrink: 0, marginTop: '0.05rem' }}>
                    {done ? '✓' : '○'}
                  </span>
                  <span style={{ fontSize: '0.67rem', color: done ? C.text : C.muted, lineHeight: 1.45 }}>
                    {criterion}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Known findings */}
      {state.known_findings?.length > 0 && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
              Known Findings
            </span>
            <span style={{ fontFamily: 'monospace', fontSize: '0.6rem', color: C.orange }}>
              {state.known_findings.length}
            </span>
          </div>
          <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: 220, overflowY: 'auto' }}>
            {state.known_findings.map((f, i) => (
              <div key={i} style={{
                fontSize: '0.67rem', color: C.text, lineHeight: 1.45,
                padding: '0.3rem 0.55rem',
                background: C.bg, border: `1px solid ${C.border}`,
                borderLeft: `2px solid ${C.orange}`, borderRadius: 4,
              }}>
                {f}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Task Board ────────────────────────────────────────────────────────────────

function TaskCard({ task }) {
  const priority = PRIORITY_COLOR[task.priority] ?? C.dim
  const status   = STATUS_COLOR[task.status]    ?? C.dim
  const cap      = CAPABILITY_COLOR[task.assigned_capability] ?? C.dim
  const capLabel = CAPABILITY_LABEL[task.assigned_capability] ?? task.assigned_capability

  return (
    <div style={{
      background: C.bg, border: `1px solid ${C.border}`,
      borderLeft: `2px solid ${priority}`,
      borderRadius: 4, padding: '0.4rem 0.6rem',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
        <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
          <span style={{ fontFamily: 'monospace', fontSize: '0.55rem', color: C.dim }}>{task.task_id}</span>
          <span style={{
            fontSize: '0.47rem', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.1em', color: priority,
            background: priority + '18', borderRadius: 2, padding: '0.05rem 0.3rem',
          }}>
            {task.priority}
          </span>
          <span style={{
            fontSize: '0.47rem', fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '0.1em', color: status,
            background: status + '18', borderRadius: 2, padding: '0.05rem 0.3rem',
          }}>
            {task.status}
          </span>
        </div>
        <span style={{
          fontSize: '0.47rem', color: cap,
          background: cap + '15', border: `1px solid ${cap + '30'}`,
          borderRadius: 2, padding: '0.05rem 0.35rem',
          textTransform: 'uppercase', letterSpacing: '0.07em',
        }}>
          {capLabel}
        </span>
      </div>
      <div style={{ fontSize: '0.67rem', color: C.text, lineHeight: 1.4, marginBottom: '0.15rem' }}>
        {task.title}
      </div>
      {task.created_from !== 'mission_decomposition' && (
        <div style={{ fontSize: '0.55rem', color: C.orange }}>
          ◆ created from {task.created_from}
        </div>
      )}
    </div>
  )
}

// ── Capability routing diagram ────────────────────────────────────────────────

function CapabilityRoutingDiagram({ tasks }) {
  const ragTasks    = tasks.filter(t => t.assigned_capability === 'agentic_rag')
  const agentTasks  = tasks.filter(t => t.assigned_capability === 'ai_agent')
  const synthTasks  = tasks.filter(t => t.assigned_capability === 'synthesis')
  const total       = tasks.length || 1

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
        fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
      }}>
        Capability Routing
      </div>
      <div style={{ padding: '0.6rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>

        {/* Orchestrator → capabilities */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{
            padding: '0.3rem 0.65rem',
            background: C.greenBg, border: `1px solid ${C.greenBrd}`,
            borderRadius: 4, fontSize: '0.58rem', fontWeight: 700, color: C.green,
            textTransform: 'uppercase', letterSpacing: '0.08em',
          }}>
            Agentic AI
          </div>
          <span style={{ color: C.dim }}>→</span>
          <div style={{ flex: 1, display: 'flex', gap: '0.4rem' }}>
            {[
              { label: 'Agentic RAG', count: ragTasks.length, color: C.cyan, bg: C.cyanBg, brd: C.cyanBrd },
              { label: 'AI Agent',    count: agentTasks.length,  color: C.blue, bg: C.blueBg, brd: C.blueBrd },
              { label: 'Synthesis',   count: synthTasks.length, color: C.orange, bg: C.orangeBg, brd: C.orangeBrd },
            ].map(cap => (
              <div key={cap.label} style={{
                flex: 1, padding: '0.3rem 0.5rem', textAlign: 'center',
                background: cap.bg, border: `1px solid ${cap.brd}`, borderRadius: 4,
              }}>
                <div style={{ fontFamily: 'monospace', fontSize: '1rem', fontWeight: 800, color: cap.color, lineHeight: 1 }}>
                  {cap.count}
                </div>
                <div style={{ fontSize: '0.47rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: C.dim, marginTop: '0.15rem' }}>
                  {cap.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Distribution bar */}
        <div style={{ display: 'flex', height: 6, borderRadius: 3, overflow: 'hidden', gap: 1 }}>
          {[
            { count: ragTasks.length,   color: C.cyan },
            { count: agentTasks.length,  color: C.blue },
            { count: synthTasks.length, color: C.orange },
          ].map(({ count, color }, i) => (
            count > 0 && (
              <div key={i} style={{
                width: `${(count / total) * 100}%`,
                background: color, opacity: 0.7,
              }} />
            )
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Intelligence center (center col) ─────────────────────────────────────────

function MissionIntelligenceCenter({ state }) {
  const tasks          = state.tasks ?? []
  const completedCount = tasks.filter(t => t.status === 'COMPLETED').length
  const criticalHighOpen = tasks.filter(t =>
    (t.priority === 'CRITICAL' || t.priority === 'HIGH') &&
    !['COMPLETED', 'DEPRIORITIZED'].includes(t.status)
  ).length
  const findingCount   = state.known_findings?.length ?? 0

  // Build a minimal nodes/edges set from tasks for the graph
  const missionGraphData = buildMissionGraph(state)

  return (
    <div className="ws-col">
      {/* KPI strip */}
      <div className="metrics-row">
        <MetricCard label="Cycles"     value={state.cycle_count}     color={C.green}  icon="⊙" sub="mission loops" />
        <MetricCard label="Tasks"      value={tasks.length}          color={C.cyan}   icon="◈" sub="total created" />
        <MetricCard label="Completed"  value={completedCount}        color={C.green}  icon="✓" sub="tasks done" />
        <MetricCard label="Open C/H"   value={criticalHighOpen}      color={criticalHighOpen > 0 ? C.orange : C.green}  icon="●" sub="critical/high" />
        <MetricCard label="Findings"   value={findingCount}          color={C.orange} icon="◆" sub="evidence pieces" />
      </div>

      {/* Relationship graph */}
      <RelationshipGraph
        result={missionGraphData}
        selectedNodeId={null}
        onNodeSelect={() => {}}
      />

      {/* Task board */}
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
      }}>
        <div style={{
          padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
            Task Board
          </span>
          <span style={{ fontFamily: 'monospace', fontSize: '0.6rem', color: C.cyan }}>
            {tasks.length} tasks
          </span>
        </div>
        <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: 320, overflowY: 'auto' }}>
          {tasks.length === 0
            ? <div style={{ fontSize: '0.65rem', color: C.dim, textAlign: 'center', padding: '1rem' }}>No tasks created yet</div>
            : tasks.map(t => <TaskCard key={t.task_id} task={t} />)
          }
        </div>
      </div>

      {/* Priority queue */}
      {state.priority_queue?.length > 0 && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
        }}>
          <div style={{
            padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Priority Queue — Next Up
          </div>
          <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            {state.priority_queue.map((tid, i) => {
              const task = tasks.find(t => t.task_id === tid)
              const priority = PRIORITY_COLOR[task?.priority] ?? C.dim
              return (
                <div key={tid} style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  padding: '0.3rem 0.5rem', background: C.bg, borderRadius: 4,
                  border: `1px solid ${C.border}`,
                }}>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.55rem', color: C.dim, width: 16 }}>
                    #{i + 1}
                  </span>
                  <div style={{ width: 5, height: 5, borderRadius: '50%', background: priority }} />
                  <span style={{ fontFamily: 'monospace', fontSize: '0.6rem', color: priority }}>{tid}</span>
                  {task && (
                    <span style={{ fontSize: '0.63rem', color: C.muted, flex: 1 }}>{task.title}</span>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Capability routing */}
      <CapabilityRoutingDiagram tasks={tasks} />
    </div>
  )
}

// ── Workflow timeline (mission events) ────────────────────────────────────────

function MissionTimeline({ events }) {
  const [showAll, setShowAll] = useState(false)

  if (!events || events.length === 0) return null

  const displayed = showAll ? events : events.slice(0, 12)

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.55rem 0.85rem', borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0,
      }}>
        <span style={{ fontSize: '0.55rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: C.muted }}>
          Workflow Timeline
        </span>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span style={{ fontFamily: 'monospace', fontSize: '0.62rem', color: C.dim }}>
            {events.length} events
          </span>
          {events.length > 12 && (
            <button
              onClick={() => setShowAll(v => !v)}
              style={{
                background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 3,
                color: C.dim, cursor: 'pointer', fontSize: '0.5rem',
                padding: '0.1rem 0.4rem', textTransform: 'uppercase', letterSpacing: '0.08em',
              }}
            >
              {showAll ? '▲ compact' : '▼ all'}
            </button>
          )}
        </div>
      </div>

      <div style={{ overflowY: 'auto', maxHeight: showAll ? 480 : 280 }}>
        {displayed.map((evt, i) => {
          const meta = WORKFLOW_EVENT_META[evt.event_type] ?? { color: C.dim, icon: '·', label: evt.event_type }
          const isLast = i === displayed.length - 1
          return (
            <div key={i} style={{
              padding: '0.4rem 0.85rem',
              borderBottom: isLast ? 'none' : `1px solid ${C.border}`,
              display: 'flex', gap: '0.6rem', alignItems: 'flex-start',
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                <span style={{ color: meta.color, fontSize: '0.72rem', lineHeight: 1, width: 14, textAlign: 'center' }}>
                  {meta.icon}
                </span>
                {!isLast && (
                  <div style={{ width: 1, flex: 1, background: C.border, marginTop: '0.3rem', minHeight: 6 }} />
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '0.58rem', fontWeight: 700, color: meta.color,
                    textTransform: 'uppercase', letterSpacing: '0.08em',
                  }}>
                    {meta.label}
                  </span>
                  {evt.task_id && (
                    <span style={{ fontFamily: 'monospace', fontSize: '0.55rem', color: C.dim }}>
                      {evt.task_id}
                    </span>
                  )}
                  <span style={{ fontFamily: 'monospace', fontSize: '0.5rem', color: C.dim, marginLeft: 'auto' }}>
                    c{evt.cycle}
                  </span>
                </div>
                <p style={{ fontSize: '0.67rem', color: C.muted, lineHeight: 1.45, marginTop: '0.1rem' }}>
                  {evt.summary}
                </p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Dynamic task creation callouts ────────────────────────────────────────────

function DynamicTaskCallouts({ tasks }) {
  const derived = tasks.filter(t => t.created_from !== 'mission_decomposition')
  if (derived.length === 0) return null

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.orangeBrd}`, borderRadius: 6, overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.45rem 0.75rem', borderBottom: `1px solid ${C.border}`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.orange }}>
          ◆ Dynamic Tasks — Created from Findings
        </span>
        <span style={{ fontFamily: 'monospace', fontSize: '0.6rem', color: C.orange }}>{derived.length}</span>
      </div>
      <div style={{ padding: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {derived.map(task => {
          const priority = PRIORITY_COLOR[task.priority] ?? C.dim
          return (
            <div key={task.task_id} style={{
              padding: '0.4rem 0.6rem',
              background: C.orangeBg, border: `1px solid ${C.orangeBrd}`,
              borderLeft: `2px solid ${C.orange}`, borderRadius: 4,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.2rem' }}>
                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.55rem', color: C.orange }}>{task.task_id}</span>
                  <span style={{
                    fontSize: '0.47rem', fontWeight: 700, textTransform: 'uppercase',
                    color: priority, background: priority + '18', borderRadius: 2, padding: '0.05rem 0.3rem',
                  }}>
                    {task.priority}
                  </span>
                </div>
                <span style={{ fontSize: '0.55rem', color: C.dim }}>
                  ← {task.created_from}
                </span>
              </div>
              <div style={{ fontSize: '0.67rem', color: C.text, lineHeight: 1.4 }}>{task.title}</div>
              {task.reason && (
                <div style={{ fontSize: '0.6rem', color: C.muted, marginTop: '0.2rem', lineHeight: 1.4 }}>
                  {task.reason}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Final assessment / READY FOR HUMAN REVIEW banner ─────────────────────────

function MissionFinalState({ state, onReset }) {
  const isReady = state.status === 'READY_FOR_HUMAN_REVIEW'
  const [expanded, setExpanded] = useState(false)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {/* Status banner */}
      <div style={{
        background: isReady ? C.greenBg : C.orangeBg,
        border: `1px solid ${isReady ? C.greenBrd : C.orangeBrd}`,
        borderRadius: 6, padding: '0.85rem 1rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: isReady ? C.green : C.orange,
            boxShadow: isReady ? `0 0 10px ${C.green}` : 'none',
          }} />
          <span style={{
            fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase',
            letterSpacing: '0.12em', color: isReady ? C.green : C.orange,
          }}>
            {isReady ? 'Mission Ready for Human Review' : 'Mission ' + state.status.replace(/_/g, ' ')}
          </span>
        </div>

        <div style={{
          padding: '0.4rem 0.65rem', marginBottom: '0.6rem',
          background: isReady ? C.bg : C.bg, border: `1px solid ${C.border}`,
          borderRadius: 4, fontSize: '0.62rem', color: C.dim,
          fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          {isReady ? '★ Investigation complete — human detective review required before any action' : state.status}
        </div>

        {/* Do NOT claim guilt / arrest */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', marginBottom: '0.6rem' }}>
          {[
            { label: 'Mission ID', value: state.mission_id, mono: true },
            { label: 'Cycles completed', value: state.cycle_count },
            { label: 'Tasks created', value: state.tasks.length },
            { label: 'Tasks completed', value: state.tasks.filter(t => t.status === 'COMPLETED').length },
            { label: 'Reassessments', value: state.reassessment_count },
          ].map(({ label, value, mono }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.6rem', color: C.muted }}>{label}</span>
              <span style={{
                fontSize: '0.62rem', color: C.text,
                fontFamily: mono ? 'monospace' : 'inherit',
              }}>
                {value}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={onReset}
            style={{
              background: 'transparent', border: `1px solid ${C.border}`,
              borderRadius: 4, padding: '0.4rem 0.75rem',
              fontSize: '0.62rem', color: C.muted, cursor: 'pointer',
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}
          >
            New Mission
          </button>
        </div>
      </div>

      {/* Final assessment */}
      {state.final_assessment && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden',
        }}>
          <button
            onClick={() => setExpanded(v => !v)}
            style={{
              width: '100%', padding: '0.45rem 0.75rem',
              background: 'transparent', border: 'none', borderBottom: expanded ? `1px solid ${C.border}` : 'none',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              cursor: 'pointer',
            }}
          >
            <span style={{ fontSize: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted }}>
              Investigation Assessment
            </span>
            <span style={{ fontSize: '0.55rem', color: C.dim }}>{expanded ? '▲' : '▼'}</span>
          </button>
          {expanded && (
            <div style={{ padding: '0.65rem 0.85rem' }}>
              <p style={{ fontSize: '0.72rem', color: C.text, lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                {state.final_assessment}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Right col (workflow + dynamic tasks + final state) ────────────────────────

function MissionWorkflowPanel({ state, onReset }) {
  return (
    <div className="ws-col">
      <MissionTimeline events={state.workflow_events} />
      <DynamicTaskCallouts tasks={state.tasks} />
      <MissionFinalState state={state} onReset={onReset} />
    </div>
  )
}

// ── Workstation header ────────────────────────────────────────────────────────

function MissionWorkstationHeader({ state, onReset }) {
  const isReady = state.status === 'READY_FOR_HUMAN_REVIEW'
  const color   = isReady ? C.green : C.orange
  return (
    <div style={{
      padding: '0.55rem 1rem',
      borderBottom: `1px solid ${C.border}`,
      background: C.panel,
      display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%', background: color,
          boxShadow: isReady ? `0 0 6px ${color}` : 'none',
        }} />
        <span style={{ fontSize: '0.62rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color }}>
          {isReady ? 'Mission Ready for Human Review' : 'Mission ' + state.status.replace(/_/g, ' ')}
        </span>
      </div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
        <MissionFlow running={false} result={state} />
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
        New Mission
      </button>
    </div>
  )
}

// ── Graph builder ─────────────────────────────────────────────────────────────

function buildMissionGraph(state) {
  const nodes = []
  const edges = []
  const tasks = state.tasks ?? []

  for (const task of tasks) {
    const cap = task.assigned_capability
    nodes.push({
      id:    task.task_id,
      label: task.task_id,
      type:  cap === 'agentic_rag' ? 'ARCHIVE' : cap === 'ai_agent' ? 'EXTERNAL' : 'SYNTHESIS',
      color: CAPABILITY_COLOR[cap] ?? C.dim,
      detail: task.title,
    })
    for (const dep of (task.dependencies ?? [])) {
      if (tasks.find(t => t.task_id === dep)) {
        edges.push({ source: dep, target: task.task_id })
      }
    }
  }

  // Extract entity nodes from findings
  const findings = state.known_findings ?? []
  for (const f of findings) {
    if (f.includes('MBK-4172') && !nodes.find(n => n.id === 'MBK-4172')) {
      nodes.push({ id: 'MBK-4172', label: 'MBK-4172', type: 'VEHICLE', color: C.blue, detail: 'Registration plate' })
    }
    if (f.includes('Marcus Vale') && !nodes.find(n => n.id === 'marcus-vale')) {
      nodes.push({ id: 'marcus-vale', label: 'Marcus Vale', type: 'PERSON', color: C.orange, detail: 'Financial recipient' })
    }
    if (f.includes('Northstar') && !nodes.find(n => n.id === 'northstar')) {
      nodes.push({ id: 'northstar', label: 'Northstar', type: 'LOCATION', color: C.cyan, detail: 'Facilities access' })
    }
  }

  // Wrap into the shape RelationshipGraph expects
  return {
    leads_discovered: nodes.map(n => ({
      label:        n.id,
      context:      n.detail ?? n.label,
      cases_found_in: [],
      search_query: n.label,
    })),
    evidence_hits: edges.map(e => ({
      case_id: e.source, source_file: '', text: `${e.source} → ${e.target}`,
      confidence: 'MEDIUM', hop: 0,
    })),
    _nodes: nodes,
    _edges: edges,
  }
}

// ── Main component ────────────────────────────────────────────────────────────

export default function AgenticAIConsole({ conn }) {
  const [mission, setMission]       = useState(BROAD_MISSION)
  const [maxCycles, setMaxCycles]   = useState(15)
  const [loading, setLoading]       = useState(false)
  const [state, setState]           = useState(null)
  const [error, setError]           = useState(null)

  const run = async () => {
    if (!mission.trim() || loading) return
    setLoading(true); setState(null); setError(null)
    try {
      const res = await fetch(`${BACKEND}/api/agentic-ai/mission`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ mission: mission.trim(), max_cycles: maxCycles }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        setError(`HTTP ${res.status}: ${err.detail || res.statusText}`)
      } else {
        setState(await res.json())
      }
    } catch (err) {
      setError(`Network error: ${String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => { setState(null); setError(null) }

  if (loading) {
    return <AgenticAILoadingState />
  }

  if (!state) {
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
        <AgenticAIPreRunState
          mission={mission}    setMission={setMission}
          maxCycles={maxCycles} setMaxCycles={setMaxCycles}
          onRun={run} loading={loading} conn={conn}
        />
      </>
    )
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <MissionWorkstationHeader state={state} onReset={reset} />
      <div className="investigation-workspace anim-slide-in">
        <MissionControl state={state} />
        <MissionIntelligenceCenter state={state} />
        <MissionWorkflowPanel state={state} onReset={reset} />
      </div>
    </div>
  )
}
