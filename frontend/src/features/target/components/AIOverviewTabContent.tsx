import { useNavigate } from 'react-router-dom';
import { SkeletonCards } from '../../../components/SkeletonLoader';
import StatusBadge from './StatusBadge';
import RiskBar from './RiskBar';

interface AIOverview {
  id: number;
  status: string;
  summary?: string;
  plan?: {
    reasoning?: string;
    objectives?: {
      id: string | number;
      description: string;
      status?: string;
      priority?: string;
    }[];
  };
  knowledge?: Record<string, unknown>;
  risk_score: number;
  business_impact?: string;
  thread_id?: number | null;
  updated_at: string;
}

interface AIOverviewTabContentProps {
  overview: AIOverview | null;
  tabLoading: boolean;
  onRefresh: () => void;
}

const AIOverviewTabContent: React.FC<AIOverviewTabContentProps> = ({ overview, tabLoading, onRefresh }) => {
  const navigate = useNavigate();

  return (
    <>
      <div className="c2-section-header">
        <span className="c2-section-title">AI STRATEGIC OVERVIEW</span>
        <button className="c2-btn c2-btn--ghost text-[0.7rem]" onClick={onRefresh}>↻ REFRESH</button>
      </div>
      {tabLoading ? (
        <SkeletonCards count={1} height={120} />
      ) : !overview ? (
        <div className="c2-empty">
          No AI analysis found.<br />
          The Celery beat task will generate overviews automatically. Check back after 30 minutes.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <div key={overview.id} className="c2-card c2-card--cyan p-5">
            <div className="flex justify-between items-start mb-3">
              <div className="flex gap-2.5 items-center">
                <StatusBadge status={overview.status} />
                {overview.business_impact && <span className="c2-badge c2-badge--amber">{overview.business_impact}</span>}
                <span className="td-mono text-[0.7rem] text-text-muted">ID #{overview.id}</span>
                {overview.thread_id && (
                  <span className="td-mono text-[0.7rem] text-text-muted ml-2">
                    Thread #{overview.thread_id}
                  </span>
                )}
              </div>
              <div className="text-right flex flex-col gap-1.5">
                <div className="mb-0 w-[140px]">
                  <div className="text-[0.65rem] text-text-muted mb-1 font-mono">RISK SCORE</div>
                  <RiskBar score={overview.risk_score} />
                </div>
                <div className="td-muted">{new Date(overview.updated_at).toLocaleString()}</div>
                <button
                  className="c2-btn c2-btn--ghost text-[0.7rem] mt-1"
                  onClick={() => navigate(`/overviews/${overview.id}`)}
                >
                  EDIT DETAILS →
                </button>
              </div>
            </div>

            {overview.summary && (
              <p className="text-[0.85rem] text-text-secondary leading-[1.6] mb-3">
                {overview.summary}
              </p>
            )}

            {overview.plan && (
              <div className="mb-3">
                <div className="font-mono text-[0.7rem] text-text-muted mb-2 uppercase">
                  ATTACK PLAN:
                </div>
                {overview.plan.reasoning && (
                  <p className="text-[0.78rem] text-text-secondary mb-2 italic">
                    {overview.plan.reasoning}
                  </p>
                )}
                {overview.plan.objectives && Array.isArray(overview.plan.objectives) && (
                  <div className="flex flex-col gap-1">
                    {overview.plan.objectives.map(obj => (
                      <div key={obj.id} className="flex gap-2.5 items-center px-2.5 py-1.5 bg-[rgba(15,23,42,0.6)] rounded border border-border-subtle">
                        <StatusBadge status={obj.status || 'PENDING'} />
                        {obj.priority && <span className="c2-badge c2-badge--amber">{obj.priority}</span>}
                        <span className="font-mono text-[0.78rem] flex-1">{obj.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {overview.knowledge && (
              <details className="mt-2">
                <summary className="cursor-pointer font-mono text-[0.7rem] text-text-muted uppercase">
                  VIEW KNOWLEDGE SNAPSHOT
                </summary>
                <pre className="mt-2 p-3 bg-[rgba(2,6,23,0.8)] rounded border border-border-subtle text-[0.72rem] text-text-secondary overflow-auto max-h-[200px]">
                  {JSON.stringify(overview.knowledge, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default AIOverviewTabContent;
