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
    <div className="flex flex-col gap-1 py-1.5 border-b border-[rgba(255,255,255,0.04)]">
      {/* Row 1: name + badges */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[#e2e8f0] text-[0.8rem] font-semibold">
          {vector.name}
        </span>
        <span style={{ ...pillBase, ...VECTOR_TYPE_STYLE[vector.vector_type] }}>
          {formatVectorType(vector.vector_type)}
        </span>
        <span style={{ ...pillBase, ...VECTOR_STATUS_STYLE[vector.status] }}>
          {vector.status}
        </span>
        {/* Risk score bar */}
        <span className="inline-flex items-center gap-1">
          <span style={{ ...pillBase, color: riskBarColor(vector.risk_score), background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.08)' }}>
            RISK {vector.risk_score}
          </span>
          <span className="w-[48px] h-1 bg-[rgba(255,255,255,0.08)] rounded overflow-hidden inline-block">
            <span style={{ display: 'block', height: '100%', width: `${barWidth}%`, background: riskBarColor(vector.risk_score), borderRadius: 2, transition: 'width 0.3s' }} />
          </span>
        </span>
      </div>

      {/* Description toggle */}
      {vector.description && (
        <button
          type="button"
          onClick={() => setShowDesc(!showDesc)}
          className="bg-transparent border-none text-[#64748b] text-[0.7rem] cursor-pointer text-left py-0.5 font-semibold"
        >
          {showDesc ? '▼' : '▶'} Description
        </button>
      )}
      {showDesc && vector.description && (
        <div className="text-[#94a3b8] text-[0.75rem] px-2 py-1 bg-[rgba(255,255,255,0.02)] rounded border border-[rgba(255,255,255,0.04)] leading-[1.5]">
          {vector.description}
        </div>
      )}

      {/* Evidence toggle */}
      {vector.evidence && (
        <button
          type="button"
          onClick={() => setShowEvidence(!showEvidence)}
          className="bg-transparent border-none text-[#64748b] text-[0.7rem] cursor-pointer text-left py-0.5 font-semibold"
        >
          {showEvidence ? '▼' : '▶'} Evidence
        </button>
      )}
      {showEvidence && vector.evidence && (
        <pre className="m-0 px-[10px] py-1.5 bg-[rgba(0,0,0,0.4)] text-[#e2e8f0] rounded text-[0.7rem] font-mono overflow-auto max-h-40 whitespace-pre-wrap break-words leading-[1.4]">
          {vector.evidence}
        </pre>
      )}
    </div>
  );
}
