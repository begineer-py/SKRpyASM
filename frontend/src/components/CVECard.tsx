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
      className="c2-card p-[14px_16px] cursor-pointer"
      onClick={() => setExpanded(v => !v)}
    >
      {/* Top row: CVE ID + badges */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex gap-[10px] items-center flex-wrap">
          <span className="font-mono text-[0.9rem] font-bold text-cyan tracking-[0.04em]">
            {cve.cve_id}
          </span>
          <CVESeverityBadge
            severity={cve.severity}
            cisaKev={cve.cisa_kev}
            exploitAvailable={cve.exploit_available}
          />
        </div>
        <span className="text-[0.7rem] text-text-muted shrink-0 ml-2">
          {expanded ? '▲' : '▼'}
        </span>
      </div>

      {/* Description */}
      <p className="text-[0.8rem] text-text-secondary m-0 mb-[10px] leading-[1.5]">
        {expanded ? cve.description : descShort}
      </p>

      {/* Metrics row */}
      <div className="flex gap-5 flex-wrap text-[0.75rem] text-text-muted">
        {cve.cvss_score !== null && (
          <span>
            CVSS:&nbsp;
            <strong style={{ color: cvssColor }}>{cve.cvss_score.toFixed(1)}</strong>
          </span>
        )}
        {cve.epss_score !== null && (
          <span>
            EPSS:&nbsp;
            <strong className="text-text-primary">{(cve.epss_score * 100).toFixed(1)}%</strong>
          </span>
        )}
        {cve.published_date && (
          <span>Published:&nbsp;<strong className="text-text-primary">{cve.published_date.slice(0, 10)}</strong></span>
        )}
        {cve.exploited_in_wild && (
          <span className="text-red font-semibold">⚠ Exploited in Wild</span>
        )}
      </div>

      {/* Expanded: affected products + references */}
      {expanded && (
        <div className="mt-3 border-t border-border-subtle pt-[10px]">
          {cve.affected_products.length > 0 && (
            <div className="mb-2">
              <div className="text-[0.7rem] text-text-muted mb-1 uppercase">
                Affected Products
              </div>
              <div className="flex flex-wrap gap-1.5">
                {cve.affected_products.map((p, i) => (
                  <span
                    key={i}
                    className="c2-badge c2-badge--muted font-mono text-[0.7rem]"
                  >
                    {p.vendor}/{p.product}{p.version ? ` ${p.version}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}

          {cve.references.length > 0 && (
            <div>
              <div className="text-[0.7rem] text-text-muted mb-1 uppercase">
                References
              </div>
              <div className="flex flex-col gap-[3px]">
                {(expanded ? cve.references : cve.references.slice(0, 2)).map((ref, i) => (
                  <a
                    key={i}
                    href={ref.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={e => e.stopPropagation()}
                    className="text-[0.72rem] text-cyan no-underline overflow-hidden text-ellipsis whitespace-nowrap block"
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
