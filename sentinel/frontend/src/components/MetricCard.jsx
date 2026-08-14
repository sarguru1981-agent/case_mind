import { C } from '../tokens'

export default function MetricCard({ label, value, color, sub, icon }) {
  const accentColor = color || C.cyan

  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderTop: `2px solid ${accentColor}`,
      borderRadius: 6,
      padding: '0.7rem 0.75rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.3rem',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background glow */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: '40%',
        background: `linear-gradient(180deg, ${accentColor}08 0%, transparent 100%)`,
        pointerEvents: 'none',
      }} />

      {/* Label */}
      <div style={{
        fontSize: '0.52rem', textTransform: 'uppercase',
        letterSpacing: '0.14em', color: C.muted,
        display: 'flex', alignItems: 'center', gap: '0.3rem',
      }}>
        {icon && <span style={{ fontSize: '0.65rem' }}>{icon}</span>}
        {label}
      </div>

      {/* Value */}
      <div style={{
        fontSize: '1.6rem', fontWeight: 800,
        color: accentColor,
        lineHeight: 1,
        fontFamily: 'SF Mono, Monaco, Inconsolata, monospace',
        letterSpacing: '-0.03em',
      }}>
        {value ?? '—'}
      </div>

      {/* Sub */}
      {sub && (
        <div style={{ fontSize: '0.6rem', color: C.dim }}>
          {sub}
        </div>
      )}
    </div>
  )
}
