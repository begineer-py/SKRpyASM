import React, { useEffect, useState } from 'react';
import { MissionReviewService } from '../services/missionReviewService';
import type { MissionReview, MissionVerdict } from '../services/missionReviewService';

const VERDICT_BADGE: Record<MissionVerdict, string> = {
  APPROVED: 'c2-badge c2-badge--green',
  REJECTED: 'c2-badge c2-badge--red',
  INCONCLUSIVE: 'c2-badge c2-badge--amber',
  PENDING: 'c2-badge c2-badge--muted',
};

interface Props {
  overviewId: number;
}

const MissionReviewList: React.FC<Props> = ({ overviewId }) => {
  const [reviews, setReviews] = useState<MissionReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    MissionReviewService.listByOverview(overviewId)
      .then((data) => {
        if (!cancelled) {
          setReviews(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Failed to load mission reviews');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [overviewId]);

  if (loading)
    return (
      <div className="text-[#64748b] p-4">Loading mission reviews...</div>
    );
  if (error)
    return (
      <div className="text-red p-4">ERROR: {error}</div>
    );
  if (reviews.length === 0)
    return (
      <div className="text-[#64748b] p-4">
        No mission reviews yet. Reviews are generated when the agent attempts to mark
        this overview as COMPLETED.
      </div>
    );

  return (
    <div className="flex flex-col gap-2">
      {reviews.map((r) => {
        const expanded = expandedId === r.id;
        return (
          <div
            key={r.id}
            className="p-3 bg-[rgba(15,23,42,0.7)] rounded-lg border border-[rgba(148,163,184,0.18)]"
          >
            <button
              onClick={() => setExpandedId(expanded ? null : r.id)}
              className="w-full bg-transparent border-none cursor-pointer text-inherit text-left p-0"
            >
              <div className="flex justify-between items-center gap-2">
                <div className="flex items-center gap-2">
                  <strong>MissionReview #{r.id}</strong>
                  <span className={VERDICT_BADGE[r.verdict]}>{r.verdict}</span>
                  {r.needs_human_review && (
                    <span className="c2-badge c2-badge--amber">
                      ⚠ NEEDS REVIEW
                    </span>
                  )}
                </div>
                <span className="text-xs text-[#94a3b8]">
                  conf {r.confidence_score}/100 · {new Date(r.created_at).toLocaleString()}
                </span>
              </div>
              <div className="text-xs text-[#64748b] mt-1.5">
                vulns: {r.vuln_count} ({r.confirmed_vuln_count} confirmed ·{' '}
                {r.high_severity_count} high) · coverage: {r.scan_coverage_pct}% ·
                triggered by: {r.triggered_by}
                {r.triggered_by_agent ? `/${r.triggered_by_agent}` : ''}
              </div>
            </button>

            {expanded && (
              <div className="mt-3 pt-3 border-t border-[rgba(148,163,184,0.18)] flex flex-col gap-3">
                <div>
                  <label className="text-[11px] text-[#94a3b8] font-semibold block mb-1">
                    ANALYSIS
                  </label>
                  <div className="text-xs text-text-primary whitespace-pre-wrap leading-[1.6]">
                    {r.reasoning || '(no reasoning provided)'}
                  </div>
                </div>

                {r.rejection_reasons.length > 0 && (
                  <div>
                    <label className="text-[11px] text-red font-semibold block mb-1">
                      REJECTION REASONS
                    </label>
                    <ul className="m-0 pl-5 text-xs text-text-primary leading-[1.6]">
                      {r.rejection_reasons.map((reason, i) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {r.suggested_actions.length > 0 && (
                  <div>
                    <label className="text-[11px] text-cyan font-semibold block mb-1">
                      SUGGESTED ACTIONS
                    </label>
                    <ul className="m-0 pl-5 text-xs text-text-primary leading-[1.6]">
                      {r.suggested_actions.map((action, i) => (
                        <li key={i}>{action}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {r.reviewed_at && (
                  <div className="text-[11px] text-[#64748b]">
                    Reviewed at: {new Date(r.reviewed_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default MissionReviewList;
