import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useHasuraQuery } from '../../../hooks/useHasuraQuery';
import { GET_SINGLE_OVERVIEW } from '../../../queries';
import { executionApi, OverviewService } from '../services/aiApi';
import type { OverviewUpdatePayload, OverviewData } from '../services/aiApi';
import MissionReviewList from '../../../components/MissionReviewList';
import PlanTab from '../components/PlanTab';
import JsonMonacoEditor from '../components/JsonMonacoEditor';
import { cn } from '@/lib/utils';

interface HasuraOverview {
  id: number;
  status: string;
  risk_score: number;
  summary?: string;
  recon_summary?: string;
  business_impact?: string;
  plan?: any;
  knowledge?: any;
  techs?: any;
  tech_stack?: any;
  subdomain_intel?: any;
  port_service?: any;
  vuln_intel?: any;
  seed_id?: number;
  created_at: string;
  updated_at: string;
  thread_id?: number;
  parent_thread_id?: number;
  core_target: {
    id: number;
    name: string;
    description?: string;
  };
}

const OverviewDetailPage: React.FC = () => {
  const { overviewId } = useParams<{ overviewId: string }>();
  const navigate = useNavigate();
  const id = parseInt(overviewId || '0');

  const { data, loading, error, refetch } = useHasuraQuery(GET_SINGLE_OVERVIEW, { id });

  const [editFields, setEditFields] = useState<OverviewUpdatePayload>({});
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'plan' | 'knowledge' | 'techs' | 'subdomain_intel' | 'port_service' | 'vuln_intel' | 'executions' | 'mission_reviews'>('summary');
  const [restData, setRestData] = useState<OverviewData | null>(null);
  const [needsHumanReview, setNeedsHumanReview] = useState(false);

  const overview: HasuraOverview | null = data?.core_overview_by_pk;

  useEffect(() => {
    if (id) {
      OverviewService.get(id)
        .then((data) => {
          setRestData(data);
          setNeedsHumanReview(
            Boolean((data as OverviewData).needs_human_review)
          );
        })
        .catch(() => {});
    }
  }, [id]);

  useEffect(() => {
    if (overview) {
      setEditFields({
        summary: overview.summary || '',
        recon_summary: overview.recon_summary || '',
        status: overview.status,
        risk_score: overview.risk_score,
        business_impact: overview.business_impact || '',
        knowledge: overview.knowledge,
        tech_stack: overview.tech_stack,
        subdomain_intel: overview.subdomain_intel,
        port_service: overview.port_service,
        vuln_intel: overview.vuln_intel,
      });
    }
  }, [overview]);

  if (loading) return <div className="h-[calc(100vh-56px)] flex items-center justify-center text-base text-slate-500 tracking-[0.2em]">LOADING_OVERVIEW_DATA...</div>;
  if (error) return <div className="h-[calc(100vh-56px)] flex items-center justify-center text-base text-red-500 tracking-[0.2em]">ERROR: {error.message}</div>;
  if (!overview) return <div className="h-[calc(100vh-56px)] flex items-center justify-center text-base text-red-500 tracking-[0.2em]">OVERVIEW_NOT_FOUND (ID: {id})</div>;

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const payload: OverviewUpdatePayload = { ...editFields };
      if (typeof payload.knowledge === 'string') {
        try { payload.knowledge = JSON.parse(payload.knowledge); } catch (e) { throw new Error('Invalid JSON in Knowledge'); }
      }
      if (typeof payload.tech_stack === 'string') {
        try { payload.tech_stack = JSON.parse(payload.tech_stack); } catch (e) { throw new Error('Invalid JSON in Tech Stack'); }
      }
      if (typeof payload.subdomain_intel === 'string') {
        try { payload.subdomain_intel = JSON.parse(payload.subdomain_intel); } catch (e) { throw new Error('Invalid JSON in Subdomain Intel'); }
      }
      if (typeof payload.port_service === 'string') {
        try { payload.port_service = JSON.parse(payload.port_service); } catch (e) { throw new Error('Invalid JSON in Port Service'); }
      }
      if (typeof payload.vuln_intel === 'string') {
        try { payload.vuln_intel = JSON.parse(payload.vuln_intel); } catch (e) { throw new Error('Invalid JSON in Vuln Intel'); }
      }

      await OverviewService.update(id, payload);
      refetch();
      alert('Overview updated successfully');
    } catch (err: any) {
      setSaveError(err.message || 'Failed to update overview');
    } finally {
      setIsSaving(false);
    }
  };

  const renderMonacoJson = (field: 'knowledge' | 'tech_stack' | 'subdomain_intel' | 'port_service' | 'vuln_intel') => {
    const val = editFields[field];
    const str = typeof val === 'string' ? val : JSON.stringify(val ?? null, null, 2);
    return (
      <JsonMonacoEditor
        value={str}
        onChange={(newStr: string) => {
          let parsed: unknown = newStr;
          try { parsed = JSON.parse(newStr); } catch { parsed = newStr; }
          setEditFields({ ...editFields, [field]: parsed });
        }}
      />
    );
  };

  const tabBtnCls = (tab: string) => cn(
    "px-6 py-3 bg-transparent border-none border-b-2 border-transparent text-slate-500 font-mono text-xs font-bold cursor-pointer transition-all duration-200 hover:text-slate-200 hover:bg-white/[0.02]",
    activeTab === tab && "text-[#00ff00] border-b-[#00ff00] bg-green-500/[0.03]"
  );

  return (
    <div className="c2-page min-h-[calc(100vh-56px)] bg-[#09090b] text-slate-200 font-mono p-8">
      <div className="flex justify-between items-center mb-6 border-b border-[rgba(0,255,0,0.1)] pb-5">
        <div className="flex items-center gap-5">
          <button className="bg-white/5 border border-white/10 text-slate-400 px-3 py-1.5 rounded cursor-pointer text-xs font-bold transition-all duration-200 hover:bg-white/10 hover:text-slate-200" onClick={() => navigate(-1)}>← BACK</button>
          <h1 className="text-2xl m-0 text-slate-200 flex items-center gap-3">
            OVERVIEW <span className="text-[#00ff00] [text-shadow:0_0_10px_rgba(0,255,0,0.3)]">#{overview.id}</span>
            <span className="text-sm text-slate-500 font-normal">@{overview.core_target.name}</span>
            {needsHumanReview && (
              <span
                className="c2-badge c2-badge--amber"
                style={{ marginLeft: 8, verticalAlign: 'middle' }}
                title="VerificationAgent flagged this overview — open Mission Reviews tab"
              >
                ⚠ NEEDS REVIEW
              </span>
            )}
          </h1>
        </div>
        <div className="header-actions">
          {saveError && <span className="text-red-500 text-xs mr-4">{saveError}</span>}
          <button
            className="bg-[rgba(0,255,0,0.1)] border border-[rgba(0,255,0,0.3)] text-[#00ff00] px-5 py-2 rounded cursor-pointer font-bold tracking-wider transition-all duration-200 hover:bg-[rgba(0,255,0,0.2)] hover:shadow-[0_0_15px_rgba(0,255,0,0.1)] disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'SAVING...' : 'SAVE_CHANGES'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-[320px_1fr] gap-6 h-[calc(100vh-180px)]">
        {/* Left Column: Metadata */}
        <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-6 flex flex-col gap-6">
          <div className="flex flex-col gap-2">
            <label className="text-[0.65rem] font-bold text-slate-600 tracking-[0.1em]">STATUS</label>
            <select
              className="bg-black border border-white/10 text-slate-200 px-3 py-2 rounded font-mono text-sm outline-none focus:border-[rgba(0,255,0,0.3)]"
              value={editFields.status || ''}
              onChange={(e) => setEditFields({ ...editFields, status: e.target.value })}
            >
              <option value="PLANNING">PLANNING</option>
              <option value="EXECUTING">EXECUTING</option>
              <option value="STALLED">STALLED</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="NEEDS_GUIDANCE">NEEDS_GUIDANCE</option>
            </select>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[0.65rem] font-bold text-slate-600 tracking-[0.1em]">RISK_SCORE (0-100)</label>
            <input
              className="bg-black border border-white/10 text-slate-200 px-3 py-2 rounded font-mono text-sm outline-none focus:border-[rgba(0,255,0,0.3)]"
              type="number"
              min="0" max="100"
              value={editFields.risk_score || 0}
              onChange={(e) => setEditFields({ ...editFields, risk_score: parseInt(e.target.value) })}
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[0.65rem] font-bold text-slate-600 tracking-[0.1em]">BUSINESS_IMPACT</label>
            <select
              className="bg-black border border-white/10 text-slate-200 px-3 py-2 rounded font-mono text-sm outline-none focus:border-[rgba(0,255,0,0.3)]"
              value={editFields.business_impact || ''}
              onChange={(e) => setEditFields({ ...editFields, business_impact: e.target.value })}
            >
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
              <option value="">N/A</option>
            </select>
          </div>

          <div className="mt-auto border-t border-white/[0.05] pt-5 flex flex-col gap-3">
            <div className="flex justify-between text-[0.7rem]">
              <span className="text-slate-600">CREATED:</span>
              <span>{new Date(overview.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-[0.7rem]">
              <span className="text-slate-600">UPDATED:</span>
              <span>{new Date(overview.updated_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-[0.7rem]">
              <span className="text-slate-600">THREAD_ID:</span>
              <code className="text-purple-500">{overview.thread_id || 'NONE'}</code>
            </div>
            <div className="flex justify-between text-[0.7rem]">
              <span className="text-slate-600">PARENT_THREAD:</span>
              <code className="text-purple-500">{overview.parent_thread_id || 'NONE'}</code>
            </div>
            <div className="flex justify-between text-[0.7rem]">
              <span className="text-slate-600">SEED_ID:</span>
              <code className="text-purple-500">{overview.seed_id || 'NONE'}</code>
            </div>
            {restData?.ips && restData.ips.length > 0 && (
              <div className="flex justify-between text-[0.7rem]" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                <span className="text-slate-600">IPS ({restData.ips.length}):</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {restData.ips.map((ipId: number) => (
                    <code key={ipId} className="text-purple-500" style={{ fontSize: 11 }}>#{ipId}</code>
                  ))}
                </div>
              </div>
            )}
            {restData?.subdomains && restData.subdomains.length > 0 && (
              <div className="flex justify-between text-[0.7rem]" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                <span className="text-slate-600">SUBDOMAINS ({restData.subdomains.length}):</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {restData.subdomains.map((sdId: number) => (
                    <code key={sdId} className="text-purple-500" style={{ fontSize: 11 }}>#{sdId}</code>
                  ))}
                </div>
              </div>
            )}
            {restData?.url_results && restData.url_results.length > 0 && (
              <div className="flex justify-between text-[0.7rem]" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                <span className="text-slate-600">URLS ({restData.url_results.length}):</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                  {restData.url_results.map((urId: number) => (
                    <code key={urId} className="text-purple-500" style={{ fontSize: 11 }}>#{urId}</code>
                  ))}
                </div>
              </div>
            )}
            {overview.thread_id && (
              <button
                className="c2-btn c2-btn--ghost"
                style={{ marginTop: 8, fontSize: '0.75rem', width: '100%' }}
                onClick={() => navigate(`/aicenter?thread=${overview.thread_id}`)}
              >
                OPEN IN AI CENTER ↗
              </button>
            )}
          </div>
        </div>

        {/* Right Column: Content Tabs */}
        <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg flex flex-col overflow-hidden">
          <div className="flex bg-black/30 border-b border-white/[0.05]">
            <button className={tabBtnCls('summary')} onClick={() => setActiveTab('summary')}>SUMMARY</button>
            <button className={tabBtnCls('plan')} onClick={() => setActiveTab('plan')}>ATTACK_PLAN</button>
            <button className={tabBtnCls('knowledge')} onClick={() => setActiveTab('knowledge')}>KNOWLEDGE_BASE</button>
            <button className={tabBtnCls('techs')} onClick={() => setActiveTab('techs')}>TECH_STACK</button>
            <button className={tabBtnCls('subdomain_intel')} onClick={() => setActiveTab('subdomain_intel')}>SUB_INTEL</button>
            <button className={tabBtnCls('port_service')} onClick={() => setActiveTab('port_service')}>PORT_SVC</button>
            <button className={tabBtnCls('vuln_intel')} onClick={() => setActiveTab('vuln_intel')}>VULN_INTEL</button>
            <button className={tabBtnCls('executions')} onClick={() => setActiveTab('executions')}>EXECUTIONS</button>
            <button className={tabBtnCls('mission_reviews')} onClick={() => setActiveTab('mission_reviews')}>
              MISSION_REVIEWS
              {needsHumanReview && (
                <span style={{ marginLeft: 6, color: 'var(--amber)', fontSize: 10 }}>●</span>
              )}
            </button>
          </div>

          <div className="flex-1 p-0 overflow-hidden">
            {activeTab === 'summary' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>SUMMARY</label>
                  <textarea
                    className="w-full h-full bg-transparent border-none text-slate-200 p-6 font-mono text-[0.95rem] leading-relaxed outline-none resize-none"
                    value={editFields.summary || ''}
                    onChange={(e) => setEditFields({ ...editFields, summary: e.target.value })}
                    placeholder="Write target summary/notes here..."
                    style={{ minHeight: 120 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>RECON SUMMARY</label>
                  <textarea
                    className="w-full h-full bg-transparent border-none text-slate-200 p-6 font-mono text-[0.95rem] leading-relaxed outline-none resize-none"
                    value={editFields.recon_summary || ''}
                    onChange={(e) => setEditFields({ ...editFields, recon_summary: e.target.value })}
                    placeholder="Reconnaissance phase summary (subdomains, open ports, tech stack)..."
                    style={{ minHeight: 120 }}
                  />
                </div>
              </div>
            )}
            {activeTab === 'plan' && (
              <PlanTab targetId={overview.core_target.id} />
            )}
            {activeTab === 'knowledge' && renderMonacoJson('knowledge')}
            {activeTab === 'techs' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>LEGACY TECHS (read-only)</label>
                  <pre style={{ background: 'rgba(15,23,42,0.5)', padding: 12, borderRadius: 6, fontSize: 12, overflow: 'auto', maxHeight: 200 }}>
                    <code>{JSON.stringify(overview.techs, null, 2) || 'N/A'}</code>
                  </pre>
                </div>
                <div>
                  <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600 }}>TECH STACK (editable JSON)</label>
                  {renderMonacoJson('tech_stack')}
                </div>
              </div>
            )}
            {activeTab === 'subdomain_intel' && (
              <div>
                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 8, display: 'block' }}>SUBDOMAIN INTEL (editable JSON)</label>
                {renderMonacoJson('subdomain_intel')}
              </div>
            )}
            {activeTab === 'port_service' && (
              <div>
                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 8, display: 'block' }}>PORT SERVICE (editable JSON)</label>
                {renderMonacoJson('port_service')}
              </div>
            )}
            {activeTab === 'vuln_intel' && (
              <div>
                <label style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 8, display: 'block' }}>VULN INTEL (editable JSON)</label>
                {renderMonacoJson('vuln_intel')}
              </div>
            )}
            {activeTab === 'executions' && overview.thread_id && (
              <OverviewExecutions threadId={overview.thread_id} />
            )}
            {activeTab === 'executions' && !overview.thread_id && (
              <div style={{ color: '#64748b', padding: 16 }}>No thread linked to this overview.</div>
            )}
            {activeTab === 'mission_reviews' && (
              <MissionReviewList overviewId={overview.id} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OverviewDetailPage;

function OverviewExecutions({ threadId }: { threadId: number }) {
  const [graphs, setGraphs] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    executionApi.listGraphs({ thread_id: threadId, limit: 20 }).then(setGraphs).catch(() => setGraphs([]));
  }, [threadId]);

  if (graphs.length === 0) return <div style={{ color: '#64748b', padding: 16 }}>No execution graphs found.</div>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {graphs.map(g => (
        <div
          key={g.id}
          style={{ padding: 12, background: 'rgba(15,23,42,0.7)', borderRadius: 8, border: '1px solid rgba(148,163,184,0.18)', cursor: 'pointer' }}
          onClick={() => navigate(`/execution-monitor?graph=${g.id}`)}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <strong>Graph #{g.id}</strong>
            <span style={{ fontSize: 12, color: '#94a3b8' }}>{g.status}</span>
          </div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            {g.assistant_id} · {new Date(g.started_at).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
}
