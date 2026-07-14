interface CVESeverityBadgeProps {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  cisaKev?: boolean;
  exploitAvailable?: boolean;
}

export default function CVESeverityBadge({
  severity,
  cisaKev,
  exploitAvailable
}: CVESeverityBadgeProps) {
  const severityClass = {
    CRITICAL: 'c2-badge--red',
    HIGH: 'c2-badge--amber',
    MEDIUM: 'c2-badge--cyan',
    LOW: 'c2-badge--muted',
  }[severity];

  return (
    <div className="flex gap-1 items-center">
      <span className={`c2-badge ${severityClass}`}>{severity}</span>
      {cisaKev && (
        <span className="c2-badge c2-badge--red" title="CISA Known Exploited Vulnerability">
          🚨 KEV
        </span>
      )}
      {exploitAvailable && (
        <span className="c2-badge c2-badge--amber" title="Public Exploit Available">
          💣 EXPLOIT
        </span>
      )}
    </div>
  );
}
