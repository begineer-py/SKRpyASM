import { useState } from 'react';
import { type CVEIntelligence } from '../services/api_cve';
import CVESeverityBadge from './CVESeverityBadge';

interface CVECardProps {
  cve: CVEIntelligence;
}

const CVSS_COLOR: Record<string, string> = {
  CRITICAL: 'var(--red)',
  HIGH: 'var(--amber)',
  MEDIUM: 'var(--cyan)',
  LOW: 'var(--text-muted)',
};

export default function CVECard({ cve }: CVECardProps) {
  const [expanded, setExpanded] = useState(false);

  const descShort = cve.description.length > 200
    ? cve.description.slice(0, 200) + '…'
    : cve.description;

  const cvssColor = CVSS_COLOR[cve.severity] ?? 'var(--text-primary)';

  return (
    <div
      className="c2-card"
      style={{ padding: '14px 16px', cursor: 'pointer' }}
      onClick={() => setExpanded(v => !v)}
    >
      {/* Top row: CVE ID + badges */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.9rem',
            fontWeight: 700,
            color: 'var(--text-cyan)',
            letterSpacing: '0.04em',
          }}>
            {cve.cve_id}
          </span>
          <CVESeverityBadge
            severity={cve.severity}
            cisaKev={cve.cisa_kev}
            exploitAvailable={cve.exploit_available}
          />
        </div>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', flexShrink: 0, marginLeft: 8 }}>
          {expanded ? '▲' : '▼'}
        </span>
      </div>

      {/* Description */}
      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: '0 0 10px', lineHeight: 1.5 }}>
        {expanded ? cve.description : descShort}
      </p>

      {/* Metrics row */}
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        {cve.cvss_score !== null && (
          <span>
            CVSS:&nbsp;
            <strong style={{ color: cvssColor }}>{cve.cvss_score.toFixed(1)}</strong>
          </span>
        )}
        {cve.epss_score !== null && (
          <span>
            EPSS:&nbsp;
            <strong style={{ color: 'var(--text-primary)' }}>{(cve.epss_score * 100).toFixed(1)}%</strong>
          </span>
        )}
        {cve.published_date && (
          <span>Published:&nbsp;<strong style={{ color: 'var(--text-primary)' }}>{cve.published_date.slice(0, 10)}</strong></span>
        )}
        {cve.exploited_in_wild && (
          <span style={{ color: 'var(--red)', fontWeight: 600 }}>⚠ Exploited in Wild</span>
        )}
      </div>

      {/* Expanded: affected products + references */}
      {expanded && (
        <div style={{ marginTop: 12, borderTop: '1px solid var(--border-color)', paddingTop: 10 }}>
          {cve.affected_products.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>
                Affected Products
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {cve.affected_products.map((p, i) => (
                  <span
                    key={i}
                    className="c2-badge c2-badge--muted"
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}
                  >
                    {p.vendor}/{p.product}{p.version ? ` ${p.version}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}

          {cve.references.length > 0 && (
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase' }}>
                References
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {(expanded ? cve.references : cve.references.slice(0, 2)).map((ref, i) => (
                  <a
                    key={i}
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    style={{
                      fontSize: '0.72rem',
                      color: 'var(--text-cyan)',
                      textDecoration: 'none',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      display: 'block',
                    }}
                  >
                    ↗ {ref.url}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
