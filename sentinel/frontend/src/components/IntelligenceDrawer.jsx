import { C } from '../tokens'

const LEAD_META = {
  northstar_facilities:   { label: 'Northstar Facilities', type: 'ORG',        color: C.orange },
  daniel_mercer:          { label: 'Daniel Mercer',        type: 'PERSON',     color: C.yellow },
  credential_nf3847:      { label: 'Credential NF-3847',   type: 'CREDENTIAL', color: C.red    },
  dark_blue_transit:      { label: 'Dark Blue Transit',    type: 'VEHICLE',    color: C.blue   },
  alarm_maintenance_mode: { label: 'Alarm Mode',           type: 'TACTIC',     color: C.orange },
  sentryguard_pattern:    { label: 'SentryGuard',          type: 'SYSTEM',     color: C.cyan   },
}

const CASE_VENUE = {
  'robbery-001': { venue: 'Hawthorne Jewellers',    color: C.cyan },
  'robbery-002': { venue: 'Millbrook Gallery',      color: C.blue },
  'robbery-003': { venue: 'Bellweather Electronics', color: C.cyan },
  'robbery-004': { venue: 'Kingsley Watches',       color: C.blue },
}

function fileToId(filename) {
  return filename.replace('.txt', '').split('-').slice(0, 2).join('-')
}

const CLOSE_BTN = {
  background: 'transparent', border: `1px solid ${C.border}`, borderRadius: 4,
  color: C.dim, cursor: 'pointer', fontSize: '0.65rem', padding: '0.2rem 0.55rem',
}

function LeadDrawer({ lead, result, onClose }) {
  const meta = LEAD_META[lead.label] || { label: lead.label, type: 'ENTITY', color: C.muted }
  const relatedHits = (result?.evidence_hits || [])
    .filter(h => lead.cases_found_in.includes(fileToId(h.source_file)))
    .slice(0, 4)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      <div style={{
        background: meta.color + '14', border: `1px solid ${meta.color + '40'}`,
        borderRadius: 6, padding: '0.75rem 0.9rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: meta.color, marginBottom: '0.3rem' }}>
              {meta.type}
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: meta.color, letterSpacing: '-0.01em' }}>
              {meta.label}
            </div>
          </div>
          <button style={CLOSE_BTN} onClick={onClose}>× close</button>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.35rem', flexWrap: 'wrap', alignItems: 'center' }}>
          {lead.cases_found_in.map(c => {
            const cv = CASE_VENUE[c] || { color: C.muted }
            return (
              <span key={c} style={{
                fontFamily: 'monospace', fontSize: '0.58rem', color: cv.color,
                background: cv.color + '18', border: `1px solid ${cv.color + '35'}`,
                borderRadius: 3, padding: '0.1rem 0.45rem',
              }}>{c}</span>
            )
          })}
          {lead.cases_found_in.length >= 2 && (
            <span style={{
              fontSize: '0.52rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em',
              color: C.orange, background: C.orangeBg, border: `1px solid ${C.orangeBrd}`,
              borderRadius: 3, padding: '0.08rem 0.4rem',
            }}>Cross-Case</span>
          )}
        </div>
      </div>

      <div style={{
        background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: '0.7rem 0.9rem',
      }}>
        <div style={{ fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted, marginBottom: '0.35rem' }}>
          Intelligence Context
        </div>
        <p style={{ fontSize: '0.78rem', color: C.text, lineHeight: 1.6 }}>{lead.context}</p>
      </div>

      {relatedHits.length > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          <div style={{
            padding: '0.5rem 0.85rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Evidence Snippets — {relatedHits.length} retrieved
          </div>
          {relatedHits.map((hit, i) => {
            const caseId = fileToId(hit.source_file)
            const cv = CASE_VENUE[caseId] || { color: C.muted }
            return (
              <div key={i} style={{
                padding: '0.55rem 0.85rem',
                borderBottom: i < relatedHits.length - 1 ? `1px solid ${C.border}` : 'none',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.58rem', color: cv.color, fontWeight: 700 }}>{caseId}</span>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.58rem', color: C.dim }}>
                    hop {hit.hop} · {(hit.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p style={{
                  fontSize: '0.72rem', color: C.muted, lineHeight: 1.55,
                  display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
                }}>{hit.text}</p>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function CaseDrawer({ caseId, result, onClose }) {
  const cv = CASE_VENUE[caseId] || { venue: caseId, color: C.muted }
  const connectedLeads = (result?.leads_discovered || []).filter(l => l.cases_found_in.includes(caseId))
  const caseHits = (result?.evidence_hits || [])
    .filter(h => fileToId(h.source_file) === caseId)
    .slice(0, 4)

  const LEAD_COLOR = {
    northstar_facilities: C.orange, daniel_mercer: C.yellow, credential_nf3847: C.red,
    dark_blue_transit: C.blue, alarm_maintenance_mode: C.orange, sentryguard_pattern: C.cyan,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      <div style={{
        background: cv.color + '14', border: `1px solid ${cv.color + '40'}`,
        borderRadius: 6, padding: '0.75rem 0.9rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontFamily: 'monospace', fontSize: '0.6rem', fontWeight: 700, color: cv.color, marginBottom: '0.25rem' }}>
              {caseId.toUpperCase()}
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: 800, color: C.white }}>{cv.venue}</div>
          </div>
          <button style={CLOSE_BTN} onClick={onClose}>× close</button>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
          <span style={{
            fontSize: '0.6rem', color: C.green, background: C.greenBg,
            border: `1px solid ${C.greenBrd}`, borderRadius: 3, padding: '0.1rem 0.5rem',
          }}>{caseHits.length} evidence hits</span>
          <span style={{
            fontSize: '0.6rem', color: C.orange, background: C.orangeBg,
            border: `1px solid ${C.orangeBrd}`, borderRadius: 3, padding: '0.1rem 0.5rem',
          }}>{connectedLeads.length} connected leads</span>
        </div>
      </div>

      {connectedLeads.length > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          <div style={{
            padding: '0.5rem 0.85rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Connected Leads
          </div>
          {connectedLeads.map((lead, i) => {
            const lColor = LEAD_COLOR[lead.label] || C.muted
            return (
              <div key={i} style={{
                padding: '0.5rem 0.85rem',
                borderBottom: i < connectedLeads.length - 1 ? `1px solid ${C.border}` : 'none',
                display: 'flex', gap: '0.5rem', alignItems: 'center',
              }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: lColor, flexShrink: 0 }} />
                <span style={{ fontSize: '0.75rem', color: C.text, fontWeight: 600 }}>
                  {lead.label.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </span>
                {lead.cases_found_in.length >= 2 && (
                  <span style={{
                    fontSize: '0.5rem', color: C.orange, background: C.orangeBg,
                    border: `1px solid ${C.orangeBrd}`, borderRadius: 3, padding: '0.05rem 0.35rem', marginLeft: 'auto',
                  }}>Cross-Case</span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {caseHits.length > 0 && (
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, overflow: 'hidden' }}>
          <div style={{
            padding: '0.5rem 0.85rem', borderBottom: `1px solid ${C.border}`,
            fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: C.muted,
          }}>
            Evidence — {caseHits.length} snippets
          </div>
          {caseHits.map((hit, i) => (
            <div key={i} style={{
              padding: '0.55rem 0.85rem',
              borderBottom: i < caseHits.length - 1 ? `1px solid ${C.border}` : 'none',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{ fontFamily: 'monospace', fontSize: '0.58rem', color: C.dim }}>hop {hit.hop}</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.58rem', color: C.dim }}>
                  {(hit.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p style={{
                fontSize: '0.72rem', color: C.muted, lineHeight: 1.55,
                display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
              }}>{hit.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function IntelligenceDrawer({ selectedNodeId, result, onClose }) {
  if (!selectedNodeId || !result) return null

  const isLead = !selectedNodeId.startsWith('robbery-')
  const lead = isLead ? result.leads_discovered?.find(l => l.label === selectedNodeId) : null
  if (isLead && !lead) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0', height: '100%' }}>
      <div style={{
        fontSize: '0.52rem', textTransform: 'uppercase', letterSpacing: '0.14em',
        color: C.cyan, padding: '0 0 0.5rem', borderBottom: `1px solid ${C.border}`,
        marginBottom: '0.6rem', flexShrink: 0,
      }}>
        Intelligence Drawer · {isLead ? 'Lead' : 'Case'}
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {isLead
          ? <LeadDrawer lead={lead} result={result} onClose={onClose} />
          : <CaseDrawer caseId={selectedNodeId} result={result} onClose={onClose} />
        }
      </div>
    </div>
  )
}
