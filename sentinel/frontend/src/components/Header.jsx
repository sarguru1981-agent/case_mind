import { C } from '../tokens'

const LBL = {
  fontSize: '0.55rem', textTransform: 'uppercase',
  letterSpacing: '0.15em',
}

export default function Header({ tab, onTab, conn }) {
  const dotColor = conn === 'connected' ? C.green : conn === 'checking' ? C.yellow : C.red

  return (
    <header style={{
      borderBottom: `1px solid ${C.borderHi}`,
      background: `linear-gradient(180deg, ${C.panel} 0%, ${C.surface} 100%)`,
      display: 'flex',
      alignItems: 'stretch',
      justifyContent: 'space-between',
      padding: '0 1.25rem',
      minHeight: 56,
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: `0 1px 0 ${C.cyanGlow}40, 0 4px 24px #00000088`,
      flexShrink: 0,
    }}>

      {/* Left: brand + nav */}
      <div style={{ display: 'flex', alignItems: 'stretch', gap: 0 }}>

        {/* Logo mark + wordmark */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.65rem',
          paddingRight: '1.5rem',
          borderRight: `1px solid ${C.border}`,
        }}>
          <div style={{
            width: 30, height: 30,
            background: `linear-gradient(135deg, ${C.cyan} 0%, ${C.blue} 100%)`,
            borderRadius: 5,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.8rem', fontWeight: 900, color: C.bg,
            flexShrink: 0,
            boxShadow: `0 0 12px ${C.cyanGlow}`,
          }}>◆</div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 800, letterSpacing: '-0.025em', lineHeight: 1 }}>
              <span style={{ color: C.white }}>Case</span>
              <span style={{ color: C.cyan }}>Mind</span>
              <span style={{ color: C.muted, fontWeight: 400, fontSize: '0.9rem' }}> Sentinel</span>
            </div>
            <div style={{ ...LBL, color: C.dim, fontSize: '0.5rem', marginTop: '0.2rem' }}>
              Police AI Investigation Platform
            </div>
          </div>
        </div>

        {/* Nav tabs */}
        <nav style={{ display: 'flex', alignItems: 'stretch', paddingLeft: '1.25rem', gap: '0.15rem' }}>
          {[
            ['investigation', 'Investigation Console'],
            ['case-analysis', 'Case Analysis'],
          ].map(([id, label]) => {
            const active = tab === id
            return (
              <button
                key={id}
                onClick={() => onTab(id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  borderBottom: `2px solid ${active ? C.cyan : 'transparent'}`,
                  color: active ? C.cyan : C.muted,
                  fontSize: '0.8rem',
                  fontWeight: active ? 600 : 400,
                  padding: '0 1rem',
                  cursor: 'pointer',
                  letterSpacing: '-0.01em',
                  transition: 'color 0.15s, border-color 0.15s',
                }}
              >
                {label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Right: operation label + status + version */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ ...LBL, color: C.cyan + '99', fontSize: '0.52rem' }}>Active Operation</div>
          <div style={{
            fontSize: '0.72rem', fontWeight: 700,
            letterSpacing: '0.06em', color: C.white,
            marginTop: '0.1rem',
          }}>
            OPERATION NIGHTFALL
          </div>
        </div>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem',
          padding: '0.3rem 0.8rem',
          background: C.cyanBg,
          border: `1px solid ${C.cyanBrd}`,
          borderRadius: 4,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            background: dotColor,
            display: 'inline-block',
            boxShadow: `0 0 6px ${dotColor}`,
          }} />
          <span style={{ ...LBL, color: C.cyan, fontSize: '0.6rem' }}>
            V0.4 · BUILD 3
          </span>
        </div>
      </div>
    </header>
  )
}
