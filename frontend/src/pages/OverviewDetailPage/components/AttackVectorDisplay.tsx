import { useState } from 'react';
import type { AttackVectorOut, VectorType, VectorStatus } from '../../../types/attackPlan';

// ─── Color Mappings ─────────────────────────────────────────────────────────

const VECTOR_TYPE_STYLE: Record<VectorType, React.CSSProperties> = {
  WEB_VULN:          { color: '#f472b6', background: 'rgba(244,114,182,0.12)', border: '1px solid rgba(244,114,182,0.3)' },
  NETWORK_EXPOSURE:  { color: '#60a5fa', background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.3)' },
  AUTH_BYPASS:       { color: '#f87171', background: 'rgba(248,113,113,0.12)', border: '1px solid rgba(248,113,113,0.3)' },
  INFO_LEAK:         { color: '#c084fc', background: 'rgba(192,132,252,0.12)', border: '1px solid rgba(192,132,252,0.3)' },
  CONFIG_ISSUE:      { color: '#fb923c', background: 'rgba(251,146,60,0.12)', border: '1px solid rgba(251,146,60,0.3)' },
  OTHER:             { color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.25)' },
};

const VECTOR_STATUS_STYLE: Record<VectorStatus, React.CSSProperties> = {
  IDENTIFIED:  { color: '#94a3b8', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.25)' },
  TESTING:     { color: '#60a5fa', background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.3)' },
  EXPLOITABLE: { color: '#ef4444', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.35)' },
  EXHAUSTED:   { color: '#475569', background: 'rgba(71,85,105,0.1)', border: '1px solid rgba(71,85,105,0.25)' },
  MITIGATED:   { color: '#00ff00', background: 'rgba(0,255,0,0.08)', border: '1px solid rgba(0,255,0,0.25)' },
};

// ─── Helpers ────────────────────────────────────────────────────────────────

const pillBase: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  padding: '2px 8px',
  fontSize: '0.65rem',
  fontWeight: 700,
  letterSpacing: '0.08em',
  borderRadius: 3,
  whiteSpace: 'nowrap',
};

function riskBarColor(score: number): string {
  if (score > 66) return '#ef4444';
  if (score >= 33) return '#f59e0b';
  return '#00ff00';
}

function formatVectorType(vt: VectorType): string {
  return vt.replace(/_/g, ' ');
}

// ─── Component ──────────────────────────────────────────────────────────────

interface AttackVectorDisplayProps {
  vector: AttackVectorOut;
}

/**
 * Compact display for a single AttackVector.
 * Shows name, vector_type badge, status badge, risk_score bar,
 * optional description, and collapsible evidence.
 */
export default function AttackVectorDisplay({ vector }: AttackVectorDisplayProps) {
  const [showEvidence, setShowEvidence] = useState(false);
  const [showDesc, setShowDesc] = useState(false);
  const barWidth = Math.min(100, Math.max(0, vector.risk_score));

  return (
    <div style={containerStyle}>
      {/* Row 1: name + badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <span style={{ color: '#e2e8f0', fontSize: '0.8rem', fontWeight: 600 }}>
          {vector.name}
        </span>
        <span style={{ ...pillBase, ...VECTOR_TYPE_STYLE[vector.vector_type] }}>
          {formatVectorType(vector.vector_type)}
        </span>
        <span style={{ ...pillBase, ...VECTOR_STATUS_STYLE[vector.status] }}>
          {vector.status}
        </span>
        {/* Risk score bar */}
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ ...pillBase, color: riskBarColor(vector.risk_score), background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)' }}>
            RISK {vector.risk_score}
          </span>
          <span style={{ width: 48, height: 4, background: 'rgba(255,255,255,0.08)', borderRadius: 2, overflow: 'hidden', display: 'inline-block' }}>
            <span style={{ display: 'block', height: '100%', width: `${barWidth}%`, background: riskBarColor(vector.risk_score), borderRadius: 2, transition: 'width 0.3s' }} />
          </span>
        </span>
      </div>

      {/* Description toggle */}
      {vector.description && (
        <button
          type="button"
          onClick={() => setShowDesc(!showDesc)}
          style={toggleBtnStyle}
        >
          {showDesc ? '▼' : '▶'} Description
        </button>
      )}
      {showDesc && vector.description && (
        <div style={descBoxStyle}>
          {vector.description}
        </div>
      )}

      {/* Evidence toggle */}
      {vector.evidence && (
        <button
          type="button"
          onClick={() => setShowEvidence(!showEvidence)}
          style={toggleBtnStyle}
        >
          {showEvidence ? '▼' : '▶'} Evidence
        </button>
      )}
      {showEvidence && vector.evidence && (
        <pre style={evidencePreStyle}>
          {vector.evidence}
        </pre>
      )}
    </div>
  );
}

// ─── Styles ─────────────────────────────────────────────────────────────────

const containerStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 4,
  padding: '6px 0',
  borderBottom: '1px solid rgba(255,255,255,0.04)',
};

const toggleBtnStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  color: '#64748b',
  fontSize: '0.7rem',
  cursor: 'pointer',
  textAlign: 'left',
  padding: '2px 0',
  fontWeight: 600,
};

const descBoxStyle: React.CSSProperties = {
  color: '#94a3b8',
  fontSize: '0.75rem',
  padding: '4px 8px',
  background: 'rgba(255,255,255,0.02)',
  borderRadius: 4,
  border: '1px solid rgba(255,255,255,0.04)',
  lineHeight: 1.5,
};

const evidencePreStyle: React.CSSProperties = {
  margin: 0,
  padding: '6px 10px',
  background: 'rgba(0,0,0,0.4)',
  color: '#e2e8f0',
  borderRadius: 4,
  fontSize: '0.7rem',
  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
  overflow: 'auto',
  maxHeight: 160,
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  lineHeight: 1.4,
};
