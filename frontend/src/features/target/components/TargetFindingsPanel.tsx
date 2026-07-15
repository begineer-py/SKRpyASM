import { useCallback, useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { VulnCard } from '../../vulnerability/components/VulnCard';
import { VulnerabilityService, type VulnerabilityData } from '../../vulnerability/services/vulnerabilityApi';

interface TargetFindingsPanelProps {
  readonly targetId: number;
}

export function TargetFindingsPanel({ targetId }: TargetFindingsPanelProps) {
  const navigate = useNavigate();
  const [findings, setFindings] = useState<readonly VulnerabilityData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFindings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await VulnerabilityService.list({ target_id: targetId, limit: 50, offset: 0 });
      setFindings(result.items);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : '無法載入此 Target 的 Findings。');
    } finally {
      setLoading(false);
    }
  }, [targetId]);

  useEffect(() => {
    void loadFindings();
  }, [loadFindings]);

  return (
    <section aria-labelledby="target-findings-heading" className="flex flex-col gap-5">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-5">
        <div>
          <h2 id="target-findings-heading" className="text-lg font-semibold text-text-primary">Findings</h2>
          <p className="mt-2 text-sm text-text-secondary">僅顯示此 Target 關聯的 Findings。</p>
        </div>
        <button className="c2-btn c2-btn--ghost" type="button" onClick={() => void loadFindings()} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} aria-hidden="true" />重新整理
        </button>
      </header>

      {error ? <p className="rounded-xl border border-red bg-bg-surface p-4 text-sm text-red" role="alert">{error}</p> : null}
      {loading ? <div className="c2-empty">正在載入 Findings…</div> : null}
      {!loading && !error && findings.length === 0 ? <div className="c2-empty">此 Target 尚無 Findings。</div> : null}
      {!loading && !error && findings.length > 0 ? (
        <div className="flex flex-col gap-3">
          {findings.map((finding) => (
            <VulnCard
              key={finding.id}
              vuln={finding}
              onOpen={() => navigate(`/vulnerabilities/${finding.id}/edit?returnTo=${encodeURIComponent(`/target/${targetId}?tab=findings`)}`)}
            />
          ))}
        </div>
      ) : null}
    </section>
  );
}
